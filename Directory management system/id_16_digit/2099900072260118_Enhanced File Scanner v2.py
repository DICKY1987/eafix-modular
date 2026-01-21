#!/usr/bin/env python3
"""
Enhanced File Scanner v2.0
A robust, cross-platform file metadata collection tool with streaming output,
resume capability, and comprehensive error handling.
"""

import os
import json
import csv
import hashlib
import mimetypes
import platform
import signal
import sys
import time
import threading
import re
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Generator, Any, Tuple
from collections import defaultdict, deque
import argparse
import logging
import gzip

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False

import uuid
import fnmatch

# =============================================================================
# USER CONFIGURATION SECTION
# Modify these settings to customize the scanner behavior
# =============================================================================

# SCAN SOURCE DIRECTORY
# Set the directory you want to scan
# Examples:
#   Windows: r"C:\Users\YourName\Documents"
#   Linux/Mac: "/home/username" or "/Users/username"
#   Current directory: "."
SCAN_PATH = r"C:\Users\richg\eafix-modular"  # Default: User's home directory

# OUTPUT DIRECTORY
# Where to save the scan results
# Examples:
#   Windows: r"C:\Users\YourName\Desktop\ScanResults"
#   Linux/Mac: "/home/username/scan_results"
#   Relative: "./scan_output"
OUTPUT_DIR = os.path.join(r"C:\Users\richg\eafix-modular", 'scan_output')

# OUTPUT FORMATS
# Choose which file formats to generate
# Options: 'json', 'ndjson', 'csv', 'markdown'
# You can specify one or multiple formats
OUTPUT_FORMATS = ['markdown', 'csv']

# HASH CALCULATION
# Set to True to calculate file checksums (slower but provides file integrity info)
INCLUDE_HASHES = False

# HASH ALGORITHMS
# Which hash algorithms to use (only applies if INCLUDE_HASHES is True)
# Options: 'md5', 'sha1', 'sha256', 'sha512'
# Note: SHA256 is recommended for security, MD5 is fastest
HASH_ALGORITHMS = ['sha256']

# FILE SIZE LIMITS
# Set maximum file size for hash calculation (in bytes)
# Large files take longer to hash. Set to 0 for no limit.
# Examples: 50MB = 50 * 1024 * 1024, 100MB = 100 * 1024 * 1024
MAX_FILE_SIZE_FOR_HASH = 100 * 1024 * 1024  # 100MB

# Minimum file size to process (0 = no minimum)
MIN_FILE_SIZE = 0

# Maximum file size to process (0 = no maximum)  
MAX_FILE_SIZE = 0

# FILTERING OPTIONS
# Exclude files containing these patterns in their names (case-insensitive)
# Examples: ['.tmp', 'cache', 'temp', '.log']
EXCLUDE_PATTERNS = []

# Exclude directories by name (case-insensitive)
# Examples: ['.git', '__pycache__', 'node_modules', 'venv', '.venv']
EXCLUDE_DIR_NAMES = ['.git', '__pycache__', 'node_modules', 'venv', '.venv']

# Include only files containing these patterns (leave empty to include all)
# If specified, only files matching these patterns will be processed
INCLUDE_PATTERNS = []

# ADVANCED OPTIONS
# Include file permissions and ownership information
INCLUDE_PERMISSIONS = True

# Include extended file attributes (Linux/Mac only)
INCLUDE_EXTENDED_ATTRS = False

# Compress output files with gzip
COMPRESS_OUTPUT = False

# Enable resume capability (can restart interrupted scans)
RESUME_FROM_CHECKPOINT = True

# Progress update interval in seconds
PROGRESS_INTERVAL = 2.0

# How often to save checkpoints (number of files)
CHECKPOINT_INTERVAL = 1000

# Maximum errors to report per error type
MAX_ERRORS_PER_TYPE = 50

# IDENTITY CONFIGURATION PATH
# Path to IDENTITY_CONFIG.yaml for ID derivation rules
IDENTITY_CONFIG_PATH = os.path.join(r"C:\Users\richg\eafix-modular\DIR_OPT\id_16_digit", '1299900079260118_IDENTITY_CONFIG.yaml')

# =============================================================================
# END OF USER CONFIGURATION
# =============================================================================

# Version and metadata
VERSION = "2.0.0"
SCANNER_ID = f"enhanced_file_scanner_v{VERSION}"

@dataclass
class ScanConfig:
    """Configuration for file scanning operations"""
    scan_path: str
    output_dir: str
    output_formats: List[str] = None  # json, ndjson, csv, markdown
    include_hashes: bool = False
    hash_algorithms: List[str] = None  # md5, sha1, sha256
    include_permissions: bool = True
    include_extended_attrs: bool = False
    max_file_size_for_hash: int = 100 * 1024 * 1024  # 100MB
    file_filters: Dict[str, Any] = None
    progress_interval: float = 2.0
    checkpoint_interval: int = 1000
    compress_output: bool = False
    resume_from_checkpoint: bool = True
    max_errors_per_type: int = 50
    parallel_hashing: bool = True
    exclude_patterns: List[str] = None
    exclude_dir_names: List[str] = None
    include_patterns: List[str] = None
    min_file_size: int = 0
    max_file_size: int = 0  # 0 means no limit
    identity_config_path: Optional[str] = None
    
    def __post_init__(self):
        if self.output_formats is None:
            self.output_formats = ['json', 'markdown']
        if self.hash_algorithms is None:
            self.hash_algorithms = ['sha256']
        if self.file_filters is None:
            self.file_filters = {}
        if self.exclude_patterns is None:
            self.exclude_patterns = []
        if self.exclude_dir_names is None:
            self.exclude_dir_names = []
        if self.include_patterns is None:
            self.include_patterns = []

@dataclass
class FileMetadata:
    """Comprehensive file metadata structure"""
    doc_id: Optional[str] = None
    relative_path: Optional[str] = None
    extension: Optional[str] = None
    path: str = ""
    name: str = ""
    size: int = 0
    modified_time: str = ""
    created_time: str = ""
    accessed_time: str = ""
    is_directory: bool = False
    is_symlink: bool = False
    permissions: Optional[str] = None
    owner: Optional[str] = None
    group: Optional[str] = None
    mime_type: Optional[str] = None
    hashes: Optional[Dict[str, str]] = None
    extended_attrs: Optional[Dict[str, str]] = None
    symlink_target: Optional[str] = None
    # NEW planning/derived fields
    content_hash: Optional[str] = None
    has_id_prefix: bool = False
    current_id_prefix: Optional[str] = None
    needs_id: bool = True
    placeholder_filename: Optional[str] = None
    type_code: Optional[str] = None
    ns_code: Optional[str] = None
    scope: Optional[str] = None
    planned_id: str = ""
    planned_rel_path: str = ""
    error: str = ""
    error_kind: str = ""

class IdentityConfigError(Exception):
    """Exception for identity config loading/validation errors."""
    pass

@dataclass
class IdentityConfig:
    """Configuration loaded from IDENTITY_CONFIG.yaml for ID derivation."""
    scope: str = "260118"
    type_table: Dict[str, str] = None
    type_fallback: str = "00"
    ns_rules: List[Tuple[str, str]] = None
    ns_fallback: str = "999"
    id_regex: str = r'^\d{16}_.+'
    delimiter_after_id: str = "_"
    content_hash_algorithm: str = "sha256"
    include_hashes: bool = False
    hash_algorithms: List[str] = None
    max_file_size_for_hash: int = 100 * 1024 * 1024

    def __post_init__(self):
        if self.type_table is None:
            self.type_table = {}
        if self.ns_rules is None:
            self.ns_rules = []
        if self.hash_algorithms is None:
            self.hash_algorithms = []

    @classmethod
    def from_yaml(cls, config_path: Path) -> 'IdentityConfig':
        """Load and validate IDENTITY_CONFIG.yaml."""
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML not installed. Run: pip install pyyaml")

        raw = yaml.safe_load(Path(config_path).read_text(encoding='utf-8'))
        profile = raw.get('profile', {}) if isinstance(raw, dict) else {}

        # Validate scope (6 digits)
        scope = str(raw.get('scope', '260118'))
        if not re.match(r'^\d{6}$', scope):
            raise IdentityConfigError(f"scope must be 6 digits, got: {scope}")

        # Build type_table
        type_table = {}
        type_fallback = "00"
        for entry in raw.get('type_classification', {}).get('table', []):
            ext = entry.get('match', '')
            code = str(entry.get('type_code', '00'))
            if not re.match(r'^\d{2}$', code):
                raise IdentityConfigError(f"type_code must be 2 digits, got: {code}")
            if ext == '*':
                type_fallback = code
            else:
                type_table[ext.lower()] = code

        # Build ns_rules
        ns_rules = []
        ns_fallback = "999"
        for entry in raw.get('namespace_routing', {}).get('rules', []):
            pattern = entry.get('path_glob', '')
            code = str(entry.get('ns_code', '999'))
            if not re.match(r'^\d{3}$', code):
                raise IdentityConfigError(f"ns_code must be 3 digits, got: {code}")
            if pattern == '**/*':
                ns_fallback = code
            else:
                ns_rules.append((pattern, code))

        id_regex = str(profile.get('id_regex', raw.get('id_regex', r'^\d{16}_.+')))
        delimiter_after_id = str(profile.get('delimiter_after_id', raw.get('delimiter_after_id', '_')))

        hashing = raw.get('hashing', {}) if isinstance(raw, dict) else {}
        content_hash_algorithm = str(hashing.get('content_hash_algorithm', 'sha256'))
        include_hashes = bool(hashing.get('include_hashes', False))
        hash_algorithms = hashing.get('hash_algorithms', [])
        max_file_size_for_hash = int(hashing.get('max_file_size_for_hash', 100 * 1024 * 1024))

        return cls(
            scope=scope,
            type_table=type_table,
            type_fallback=type_fallback,
            ns_rules=ns_rules,
            ns_fallback=ns_fallback,
            id_regex=id_regex,
            delimiter_after_id=delimiter_after_id,
            content_hash_algorithm=content_hash_algorithm,
            include_hashes=include_hashes,
            hash_algorithms=hash_algorithms,
            max_file_size_for_hash=max_file_size_for_hash,
        )

    def derive_type_code(self, extension: str, is_directory: bool = False) -> str:
        """Derive TYPE code from extension."""
        if is_directory:
            return "00"
        ext_key = f'.{extension.lower()}' if extension else '*'
        return self.type_table.get(ext_key, self.type_fallback)

    def derive_ns_code(self, relative_path: str) -> str:
        """Derive NS code from relative path using glob rules."""
        path = relative_path.replace('\\', '/')
        for pattern, ns_code in self.ns_rules:
            if fnmatch.fnmatch(path, pattern):
                return ns_code
        return self.ns_fallback

    def extract_doc_id(self, filename: str) -> Optional[str]:
        """Extract a 16-digit ID prefix using configured delimiter."""
        delimiter = self.delimiter_after_id or "_"
        pattern = rf'^(?P<doc_id>\d{{16}}){re.escape(delimiter)}'
        match = re.match(pattern, filename)
        if match:
            return match.group('doc_id')
        return None

class ProgressTracker:
    """Rolling average progress tracker without pre-scanning"""
    def __init__(self, update_interval: float = 2.0):
        self.update_interval = update_interval
        self.start_time = time.time()
        self.last_update = self.start_time
        self.processed_files = 0
        self.processed_dirs = 0
        self.total_size = 0
        self.error_counts = defaultdict(int)
        self.recent_rates = deque(maxlen=10)  # Keep last 10 rates for smoothing
        
    def update(self, files_delta: int = 0, dirs_delta: int = 0, size_delta: int = 0):
        """Update counters and maybe display progress"""
        self.processed_files += files_delta
        self.processed_dirs += dirs_delta
        self.total_size += size_delta
        
        now = time.time()
        if now - self.last_update >= self.update_interval:
            self._display_progress(now)
            self.last_update = now
    
    def _display_progress(self, now: float):
        """Display current progress with rolling average rate"""
        elapsed = now - self.start_time
        if elapsed < 1:
            return
            
        current_rate = self.processed_files / elapsed
        self.recent_rates.append(current_rate)
        smooth_rate = sum(self.recent_rates) / len(self.recent_rates)
        
        size_mb = self.total_size / (1024 * 1024)
        
        print(f"[PROGRESS] Files: {self.processed_files:,} | "
              f"Dirs: {self.processed_dirs:,} | "
              f"Size: {size_mb:.1f}MB | "
              f"Rate: {smooth_rate:.1f} files/sec | "
              f"Elapsed: {self._format_time(elapsed)}")
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as human-readable time"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds//60:.0f}m{seconds%60:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h{minutes:.0f}m"
    
    def add_error(self, error_type: str):
        """Record an error for statistics"""
        self.error_counts[error_type] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get final summary statistics"""
        elapsed = time.time() - self.start_time
        return {
            'files_processed': self.processed_files,
            'directories_processed': self.processed_dirs,
            'total_size_bytes': self.total_size,
            'elapsed_seconds': elapsed,
            'average_rate': self.processed_files / elapsed if elapsed > 0 else 0,
            'error_counts': dict(self.error_counts)
        }

class CheckpointManager:
    """Manages scan checkpoints for resume capability"""
    def __init__(self, checkpoint_file: str, interval: int = 1000):
        self.checkpoint_file = checkpoint_file
        self.interval = interval
        self.processed_paths = set()
        self.files_since_checkpoint = 0
        
    def load_checkpoint(self) -> set:
        """Load processed paths from checkpoint file"""
        if not os.path.exists(self.checkpoint_file):
            return set()
            
        try:
            with open(self.checkpoint_file, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        except Exception as e:
            logging.warning(f"Could not load checkpoint: {e}")
            return set()
    
    def save_checkpoint(self, path: str):
        """Add path to checkpoint and maybe save"""
        self.processed_paths.add(path)
        self.files_since_checkpoint += 1
        
        if self.files_since_checkpoint >= self.interval:
            self._write_checkpoint()
            self.files_since_checkpoint = 0
    
    def _write_checkpoint(self):
        """Write checkpoint to disk"""
        try:
            with open(self.checkpoint_file, 'w') as f:
                for path in sorted(self.processed_paths):
                    f.write(f"{path}\n")
        except Exception as e:
            logging.error(f"Could not save checkpoint: {e}")
    
    def cleanup(self):
        """Remove checkpoint file on successful completion"""
        try:
            os.remove(self.checkpoint_file)
        except OSError:
            pass

class EnhancedFileScanner:
    """Main scanner class with streaming output and resume capability"""
    
    _DOC_ID_RE = re.compile(r'^(?P<doc_id>\d{16})_')
    
    def __init__(self, config: ScanConfig):
        self.config = config
        self.should_stop = False
        self.progress = ProgressTracker(config.progress_interval)
        self.checkpoint_manager = None
        self.output_writers = {}
        self.identity_config = None
        self.scan_id = None
        self.scan_root = None
        self.first_seen_utc = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Create output directory and setup logging
        self._setup_output_directory()
        self.logger = self._setup_logging()
        
        # Load identity config
        if config.identity_config_path:
            self._load_identity_config(config.identity_config_path)
        
    def _setup_output_directory(self):
        """Create output directory if it doesn't exist"""
        os.makedirs(self.config.output_dir, exist_ok=True)
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging with file and console output"""
        logger = logging.getLogger(SCANNER_ID)
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # File handler
        log_file = os.path.join(self.config.output_dir, 'scanner.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def _load_identity_config(self, config_path: str):
        """Load IDENTITY_CONFIG.yaml for derivation rules."""
        try:
            self.identity_config = IdentityConfig.from_yaml(config_path)
            self.logger.info(f"Loaded identity config: scope={self.identity_config.scope}")
            self._apply_identity_hashing_defaults()
        except (IdentityConfigError, FileNotFoundError, ImportError) as e:
            self.logger.warning(f"Identity config error: {e}. Using defaults.")
            self.identity_config = IdentityConfig()

    def _apply_identity_hashing_defaults(self):
        """Apply hashing defaults from identity config when not overridden."""
        if not self.identity_config:
            return

        if self.config.include_hashes == INCLUDE_HASHES:
            self.config.include_hashes = self.identity_config.include_hashes

        if self.identity_config.hash_algorithms and self.config.hash_algorithms == HASH_ALGORITHMS:
            self.config.hash_algorithms = self.identity_config.hash_algorithms

        if self.config.max_file_size_for_hash == MAX_FILE_SIZE_FOR_HASH:
            self.config.max_file_size_for_hash = self.identity_config.max_file_size_for_hash
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.should_stop = True
    
    def scan(self) -> bool:
        """Main scanning method with full error handling"""
        try:
            self._validate_config()
            self._initialize_output_writers()
            
            if self.config.resume_from_checkpoint:
                self.checkpoint_manager = CheckpointManager(
                    os.path.join(self.config.output_dir, 'checkpoint.txt'),
                    self.config.checkpoint_interval
                )
                processed_paths = self.checkpoint_manager.load_checkpoint()
                self.logger.info(f"Resuming scan, skipping {len(processed_paths)} already processed paths")
            else:
                processed_paths = set()
            
            # Start the scan
            self.logger.info(f"Starting scan of: {self.config.scan_path}")
            self.logger.info(f"Output formats: {', '.join(self.config.output_formats)}")
            
            scan_successful = self._perform_scan(processed_paths)
            
            if scan_successful and not self.should_stop:
                self._finalize_outputs()
                self._generate_summary_report()
                if self.checkpoint_manager:
                    self.checkpoint_manager.cleanup()
                self.logger.info("Scan completed successfully!")
                return True
            else:
                self.logger.warning("Scan was interrupted or failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Fatal error during scan: {e}", exc_info=True)
            return False
        finally:
            self._cleanup_outputs()
    
    def _validate_config(self):
        """Validate configuration parameters"""
        if not os.path.exists(self.config.scan_path):
            raise ValueError(f"Scan path does not exist: {self.config.scan_path}")
        
        if not os.path.isdir(self.config.scan_path):
            raise ValueError(f"Scan path is not a directory: {self.config.scan_path}")
        
        # Validate output formats
        valid_formats = {'json', 'ndjson', 'csv', 'markdown'}
        invalid_formats = set(self.config.output_formats) - valid_formats
        if invalid_formats:
            raise ValueError(f"Invalid output formats: {invalid_formats}")
        
        # Validate hash algorithms
        if self.config.include_hashes:
            valid_algos = {'md5', 'sha1', 'sha256', 'sha512'}
            invalid_algos = set(self.config.hash_algorithms) - valid_algos
            if invalid_algos:
                raise ValueError(f"Invalid hash algorithms: {invalid_algos}")
    
    def _initialize_output_writers(self):
        """Initialize output file writers for each format"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"file_scan_{timestamp}"
        
        # Generate per-run metadata
        self.scan_id = f"{timestamp}_{uuid.uuid4().hex[:12]}"
        self.scan_root = os.path.abspath(self.config.scan_path)
        self.first_seen_utc = datetime.now(timezone.utc).isoformat()
        
        for fmt in self.config.output_formats:
            if fmt == 'json':
                self._init_json_writer(base_name)
            elif fmt == 'ndjson':
                self._init_ndjson_writer(base_name)
            elif fmt == 'csv':
                self._init_csv_writer(base_name)
            elif fmt == 'markdown':
                self._init_markdown_writer(base_name)
    
    def _init_json_writer(self, base_name: str):
        """Initialize JSON array writer"""
        filename = f"{base_name}.json"
        if self.config.compress_output:
            filename += ".gz"
            file_obj = gzip.open(os.path.join(self.config.output_dir, filename), 'wt')
        else:
            file_obj = open(os.path.join(self.config.output_dir, filename), 'w')
        
        file_obj.write('[\n')
        self.output_writers['json'] = {
            'file': file_obj,
            'first_entry': True,
            'filename': filename
        }
    
    def _init_ndjson_writer(self, base_name: str):
        """Initialize newline-delimited JSON writer"""
        filename = f"{base_name}.ndjson"
        if self.config.compress_output:
            filename += ".gz"
            file_obj = gzip.open(os.path.join(self.config.output_dir, filename), 'wt')
        else:
            file_obj = open(os.path.join(self.config.output_dir, filename), 'w')
        
        self.output_writers['ndjson'] = {
            'file': file_obj,
            'filename': filename
        }
    
    def _init_csv_writer(self, base_name: str):
        """Initialize CSV writer"""
        filename = f"{base_name}.csv"
        if self.config.compress_output:
            filename += ".gz"
            file_obj = gzip.open(os.path.join(self.config.output_dir, filename), 'wt', newline='')
        else:
            file_obj = open(os.path.join(self.config.output_dir, filename), 'w', newline='')
        
        # Write CSV header with full 26-column schema
        fieldnames = [
            'scan_id', 'scan_root', 'first_seen_utc',
            'relative_path', 'path', 'name', 'extension',
            'size_bytes', 'mtime_utc', 'created_time',
            'is_directory', 'mime_type', 'permissions', 'content_hash',
            'doc_id', 'has_id_prefix', 'current_id_prefix', 'needs_id',
            '0000000000000000_filename',
            'type_code', 'ns_code', 'scope',
            'planned_id', 'planned_rel_path',
            'error', 'error_kind'
        ]
        
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        
        self.output_writers['csv'] = {
            'file': file_obj,
            'writer': writer,
            'filename': filename
        }
    
    def _init_markdown_writer(self, base_name: str):
        """Initialize Markdown report writer"""
        filename = f"{base_name}.md"
        file_obj = open(os.path.join(self.config.output_dir, filename), 'w')
        
        # Write markdown header
        file_obj.write(f"# File Scan Report\n\n")
        file_obj.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
        file_obj.write(f"**Scan Path:** `{self.config.scan_path}`\n\n")
        file_obj.write(f"**Scanner Version:** {VERSION}\n\n")
        file_obj.write("## Configuration\n\n")
        file_obj.write(f"- Include Hashes: {self.config.include_hashes}\n")
        file_obj.write(f"- Hash Algorithms: {', '.join(self.config.hash_algorithms)}\n")
        file_obj.write(f"- Include Permissions: {self.config.include_permissions}\n")
        file_obj.write("\n## Scan Progress\n\n")
        
        # Inventory table (streamed; one row per file)
        file_obj.write("## Inventory\n\n")
        file_obj.write("| doc_id | relative_path | size | modified_utc | mime_type | perms |\n")
        file_obj.write("|---|---|---:|---|---|---|\n")
        
        self.output_writers['markdown'] = {
            'file': file_obj,
            'filename': filename
        }
    
    def _perform_scan(self, skip_paths: set) -> bool:
        """Perform the actual directory traversal and file processing"""
        try:
            # Normalize output dir for exclusion check
            output_dir_abs = os.path.abspath(self.config.output_dir)
            
            for root, dirs, files in os.walk(self.config.scan_path):
                if self.should_stop:
                    break
                
                if self._should_skip_directory(
                    root=root,
                    dirs=dirs,
                    skip_paths=skip_paths,
                    output_dir_abs=output_dir_abs
                ):
                    continue
                
                self._filter_dirs(dirs)
                
                self._process_directory(root)
                self.progress.update(dirs_delta=1)
                
                self._process_files_in_dir(root, files, skip_paths)
                
                if self.checkpoint_manager:
                    self.checkpoint_manager.save_checkpoint(root)
            
            return not self.should_stop
            
        except Exception as e:
            self.logger.error(f"Error during directory traversal: {e}", exc_info=True)
            return False

    def _should_skip_directory(
        self,
        root: str,
        dirs: List[str],
        skip_paths: set,
        output_dir_abs: str
    ) -> bool:
        """Return True and prune dirs if a directory should be skipped"""
        if root in skip_paths:
            dirs[:] = []  # Prune subtree
            return True
        
        if os.path.abspath(root).startswith(output_dir_abs):
            dirs[:] = []  # Prune subtree
            return True
        
        return False
    
    def _filter_dirs(self, dirs: List[str]) -> None:
        """Filter out excluded directory names"""
        if not self.config.exclude_dir_names:
            return
        
        excluded = {name.lower() for name in self.config.exclude_dir_names}
        dirs[:] = [d for d in dirs if d.lower() not in excluded]
    
    def _process_files_in_dir(
        self,
        root: str,
        files: List[str],
        skip_paths: set
    ) -> None:
        """Process files in a directory"""
        for filename in files:
            if self.should_stop:
                break
            
            file_path = os.path.join(root, filename)
            
            if file_path in skip_paths:
                continue
            
            if not self._should_process_file(file_path, filename):
                continue
            
            metadata = self._process_file(file_path)
            if metadata:
                self._write_to_outputs(metadata)
                if self.checkpoint_manager:
                    self.checkpoint_manager.save_checkpoint(file_path)
                
                self.progress.update(files_delta=1, size_delta=metadata.size)
    
    def _should_process_file(self, file_path: str, filename: str) -> bool:
        """Apply file filters to determine if file should be processed"""
        try:
            # Size filters
            if self.config.min_file_size > 0 or self.config.max_file_size > 0:
                file_size = os.path.getsize(file_path)
                if self.config.min_file_size > 0 and file_size < self.config.min_file_size:
                    return False
                if self.config.max_file_size > 0 and file_size > self.config.max_file_size:
                    return False
            
            # Pattern filters
            if self.config.exclude_patterns:
                for pattern in self.config.exclude_patterns:
                    if pattern in filename.lower():
                        return False
            
            if self.config.include_patterns:
                included = False
                for pattern in self.config.include_patterns:
                    if pattern in filename.lower():
                        included = True
                        break
                if not included:
                    return False
            
            return True
            
        except OSError:
            return False
    
    def _process_directory(self, dir_path: str):
        """Process directory metadata"""
        try:
            stat_info = os.stat(dir_path)
            metadata = FileMetadata(
                path=dir_path,
                name=os.path.basename(dir_path) or dir_path,
                size=0,  # Directories don't have meaningful size
                modified_time=datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc).isoformat(),
                created_time=datetime.fromtimestamp(stat_info.st_ctime, tz=timezone.utc).isoformat(),
                accessed_time=datetime.fromtimestamp(stat_info.st_atime, tz=timezone.utc).isoformat(),
                is_directory=True
            )
            
            if self.config.include_permissions:
                metadata.permissions = oct(stat_info.st_mode)[-3:]
                if hasattr(stat_info, 'st_uid') and PSUTIL_AVAILABLE:
                    try:
                        import pwd
                        metadata.owner = pwd.getpwuid(stat_info.st_uid).pw_name
                    except (ImportError, KeyError):
                        pass
            
            self._write_to_outputs(metadata)
            
        except OSError as e:
            self.progress.add_error('directory_access')
            if self.progress.error_counts['directory_access'] <= self.config.max_errors_per_type:
                self.logger.warning(f"Could not access directory {dir_path}: {e}")
    
    def _process_file(self, file_path: str) -> Optional[FileMetadata]:
        """Process individual file and extract metadata"""
        try:
            stat_info = os.stat(file_path)
            
            metadata = FileMetadata(
                path=file_path,
                name=os.path.basename(file_path),
                size=stat_info.st_size,
                modified_time=datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc).isoformat(),
                created_time=datetime.fromtimestamp(stat_info.st_ctime, tz=timezone.utc).isoformat(),
                accessed_time=datetime.fromtimestamp(stat_info.st_atime, tz=timezone.utc).isoformat(),
                is_directory=False,
                is_symlink=os.path.islink(file_path)
            )
            
            # Registry-ready fields
            metadata.relative_path = os.path.relpath(file_path, self.config.scan_path)
            metadata.extension = Path(file_path).suffix.lstrip('.').lower() if Path(file_path).suffix else ''
            doc_id = None
            if self.identity_config:
                doc_id = self.identity_config.extract_doc_id(metadata.name)
            else:
                m = self._DOC_ID_RE.match(metadata.name)
                if m:
                    doc_id = m.group('doc_id')
            
            # ID prefix detection
            if doc_id:
                metadata.doc_id = doc_id
                metadata.has_id_prefix = True
                metadata.current_id_prefix = metadata.doc_id
                metadata.needs_id = False
                metadata.placeholder_filename = metadata.name
            else:
                metadata.doc_id = ""
                metadata.has_id_prefix = False
                metadata.current_id_prefix = ""
                metadata.needs_id = True
                metadata.placeholder_filename = f"0000000000000000_{metadata.name}"
            
            # Config-driven derivations
            if self.identity_config:
                metadata.type_code = self.identity_config.derive_type_code(metadata.extension, metadata.is_directory)
                metadata.ns_code = self.identity_config.derive_ns_code(metadata.relative_path)
                metadata.scope = self.identity_config.scope
            else:
                metadata.type_code = "00"
                metadata.ns_code = "999"
                metadata.scope = "000000"
            
            # Get MIME type
            metadata.mime_type, _ = mimetypes.guess_type(file_path)
            
            # Handle symlinks
            if metadata.is_symlink:
                try:
                    metadata.symlink_target = os.readlink(file_path)
                except OSError:
                    pass
            
            # Get permissions and ownership
            if self.config.include_permissions:
                metadata.permissions = oct(stat_info.st_mode)[-3:]
                if hasattr(stat_info, 'st_uid') and PSUTIL_AVAILABLE:
                    try:
                        import pwd, grp
                        metadata.owner = pwd.getpwuid(stat_info.st_uid).pw_name
                        metadata.group = grp.getgrgid(stat_info.st_gid).gr_name
                    except (ImportError, KeyError):
                        pass
            
            # Calculate file hashes if requested
            if (self.config.include_hashes and 
                stat_info.st_size <= self.config.max_file_size_for_hash and
                not metadata.is_symlink):
                metadata.hashes = self._calculate_hashes(file_path)
                if metadata.hashes:
                    algo = self.identity_config.content_hash_algorithm if self.identity_config else 'sha256'
                    content_hash = metadata.hashes.get(algo)
                    if not content_hash:
                        content_hash = next(iter(metadata.hashes.values()), None)
                    metadata.content_hash = content_hash
            
            return metadata
            
        except PermissionError:
            self.progress.add_error('permission_denied')
            if self.progress.error_counts['permission_denied'] <= self.config.max_errors_per_type:
                self.logger.warning(f"Permission denied: {file_path}")
        except OSError as e:
            self.progress.add_error('file_access')
            if self.progress.error_counts['file_access'] <= self.config.max_errors_per_type:
                self.logger.warning(f"Could not access file {file_path}: {e}")
        except Exception as e:
            self.progress.add_error('unexpected')
            self.logger.error(f"Unexpected error processing {file_path}: {e}")
        
        return None
    
    def _calculate_hashes(self, file_path: str) -> Dict[str, str]:
        """Calculate file hashes for specified algorithms"""
        hashes = {}
        hash_objects = {}
        
        # Initialize hash objects
        for algo in self.config.hash_algorithms:
            hash_objects[algo] = hashlib.new(algo)
        
        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files efficiently
                chunk_size = 64 * 1024  # 64KB chunks
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    for hash_obj in hash_objects.values():
                        hash_obj.update(chunk)
            
            # Get final hash values
            for algo, hash_obj in hash_objects.items():
                hashes[algo] = hash_obj.hexdigest()
                
        except OSError as e:
            self.logger.warning(f"Could not hash file {file_path}: {e}")
        
        return hashes
    
    def _write_to_outputs(self, metadata: FileMetadata):
        """Write metadata to all configured output formats"""
        try:
            # Convert to dictionary for easier handling
            data = asdict(metadata)
            
            # Write to JSON
            if 'json' in self.output_writers:
                self._write_json_entry(data)
            
            # Write to NDJSON
            if 'ndjson' in self.output_writers:
                self._write_ndjson_entry(data)
            
            # Write to CSV
            if 'csv' in self.output_writers:
                self._write_csv_row(data)
            
            # Write to Markdown (files only; avoid huge directory spam)
            if 'markdown' in self.output_writers:
                self._write_markdown_row(data)
            
        except Exception as e:
            self.logger.error(f"Error writing output for {metadata.path}: {e}")

    def _write_json_entry(self, data: Dict[str, Any]) -> None:
        """Write one JSON entry"""
        writer = self.output_writers['json']
        if not writer['first_entry']:
            writer['file'].write(',\n')
        json.dump(data, writer['file'], indent=2)
        writer['first_entry'] = False

    def _write_ndjson_entry(self, data: Dict[str, Any]) -> None:
        """Write one NDJSON entry"""
        writer = self.output_writers['ndjson']
        writer['file'].write(json.dumps(data) + '\n')

    def _write_csv_row(self, data: Dict[str, Any]) -> None:
        """Write one CSV row"""
        writer = self.output_writers['csv']
        csv_row = {
            'scan_id': self.scan_id or '',
            'scan_root': self.scan_root or '',
            'first_seen_utc': self.first_seen_utc or '',
            'relative_path': data.get('relative_path', ''),
            'path': data['path'],
            'name': data['name'],
            'extension': data.get('extension', ''),
            'size_bytes': data['size'],
            'mtime_utc': data['modified_time'],
            'created_time': data['created_time'],
            'is_directory': data['is_directory'],
            'mime_type': data.get('mime_type', ''),
            'permissions': data.get('permissions', ''),
            'content_hash': data.get('content_hash', ''),
            'doc_id': data.get('doc_id', ''),
            'has_id_prefix': data.get('has_id_prefix', False),
            'current_id_prefix': data.get('current_id_prefix', ''),
            'needs_id': data.get('needs_id', True),
            '0000000000000000_filename': data.get('placeholder_filename', ''),
            'type_code': data.get('type_code', ''),
            'ns_code': data.get('ns_code', ''),
            'scope': data.get('scope', ''),
            'planned_id': data.get('planned_id', ''),
            'planned_rel_path': data.get('planned_rel_path', ''),
            'error': data.get('error', ''),
            'error_kind': data.get('error_kind', '')
        }
        
        writer['writer'].writerow(csv_row)

    def _write_markdown_row(self, data: Dict[str, Any]) -> None:
        """Write one Markdown row (files only)"""
        if data.get('is_directory', False):
            return
        
        md = self.output_writers['markdown']['file']
        doc_id = data.get('doc_id') or ""
        rel = (data.get('relative_path') or data.get('path') or "").replace("\\", "/")
        size = data.get('size', 0)
        mtime = data.get('modified_time', "")
        mime = data.get('mime_type') or ""
        perms = data.get('permissions') or ""
        # basic escaping for markdown tables
        rel = rel.replace("|", "\\|")
        mime = mime.replace("|", "\\|")
        md.write(f"| {doc_id} | `{rel}` | {size} | {mtime} | {mime} | {perms} |\n")
    
    def _finalize_outputs(self):
        """Finalize output files"""
        # Flush all writers before closing
        for writer_info in self.output_writers.values():
            try:
                writer_info['file'].flush()
            except:
                pass
        
        # Close JSON array
        if 'json' in self.output_writers:
            self.output_writers['json']['file'].write('\n]')
        
        # Add summary to markdown
        if 'markdown' in self.output_writers:
            summary = self.progress.get_summary()
            md_file = self.output_writers['markdown']['file']
            md_file.write("\n## Scan Summary\n\n")
            md_file.write(f"- **Files Processed:** {summary['files_processed']:,}\n")
            md_file.write(f"- **Directories Processed:** {summary['directories_processed']:,}\n")
            md_file.write(f"- **Total Size:** {summary['total_size_bytes'] / (1024**3):.2f} GB\n")
            md_file.write(f"- **Elapsed Time:** {summary['elapsed_seconds']:.1f} seconds\n")
            md_file.write(f"- **Average Rate:** {summary['average_rate']:.1f} files/second\n")
            
            if summary['error_counts']:
                md_file.write("\n### Errors Encountered\n\n")
                for error_type, count in summary['error_counts'].items():
                    md_file.write(f"- **{error_type}:** {count:,}\n")
    
    def _cleanup_outputs(self):
        """Close all output files"""
        for writer_info in self.output_writers.values():
            try:
                writer_info['file'].close()
            except:
                pass
    
    def _generate_summary_report(self):
        """Generate final summary report"""
        summary = self.progress.get_summary()
        
        self.logger.info("=" * 50)
        self.logger.info("SCAN COMPLETE - SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Files processed: {summary['files_processed']:,}")
        self.logger.info(f"Directories processed: {summary['directories_processed']:,}")
        self.logger.info(f"Total size: {summary['total_size_bytes'] / (1024**3):.2f} GB")
        self.logger.info(f"Elapsed time: {summary['elapsed_seconds']:.1f} seconds")
        self.logger.info(f"Average rate: {summary['average_rate']:.1f} files/second")
        
        if summary['error_counts']:
            self.logger.info("\nErrors encountered:")
            for error_type, count in summary['error_counts'].items():
                self.logger.info(f"  {error_type}: {count:,}")
        
        self.logger.info("\nOutput files generated:")
        for writer_info in self.output_writers.values():
            output_path = os.path.join(self.config.output_dir, writer_info['filename'])
            file_size = os.path.getsize(output_path) / (1024**2)  # MB
            self.logger.info(f"  {writer_info['filename']} ({file_size:.1f} MB)")

def create_user_config() -> ScanConfig:
    """Create configuration from user-defined constants"""
    return ScanConfig(
        scan_path=os.path.abspath(SCAN_PATH),
        output_dir=os.path.abspath(OUTPUT_DIR),
        output_formats=OUTPUT_FORMATS,
        include_hashes=INCLUDE_HASHES,
        hash_algorithms=HASH_ALGORITHMS,
        include_permissions=INCLUDE_PERMISSIONS,
        include_extended_attrs=INCLUDE_EXTENDED_ATTRS,
        max_file_size_for_hash=MAX_FILE_SIZE_FOR_HASH,
        min_file_size=MIN_FILE_SIZE,
        max_file_size=MAX_FILE_SIZE,
        exclude_patterns=[p.lower() for p in EXCLUDE_PATTERNS],
        exclude_dir_names=[d.lower() for d in EXCLUDE_DIR_NAMES],
        include_patterns=[p.lower() for p in INCLUDE_PATTERNS],
        progress_interval=PROGRESS_INTERVAL,
        checkpoint_interval=CHECKPOINT_INTERVAL,
        compress_output=COMPRESS_OUTPUT,
        resume_from_checkpoint=RESUME_FROM_CHECKPOINT,
        max_errors_per_type=MAX_ERRORS_PER_TYPE
    )

def create_default_config() -> ScanConfig:
    """Create default configuration (fallback)"""
    # Use platform-appropriate default paths
    if platform.system() == "Windows":
        default_output = os.path.join(os.path.expanduser('~'), 'Documents', 'FileScanOutput')
    else:
        default_output = os.path.join(os.path.expanduser('~'), 'file_scan_output')
    
    return ScanConfig(
        scan_path=os.path.expanduser('~'),
        output_dir=default_output,
        output_formats=['json', 'markdown'],
        include_hashes=False,
        hash_algorithms=['sha256'],
        include_permissions=True,
        max_file_size_for_hash=50 * 1024 * 1024,  # 50MB
        progress_interval=2.0,
        checkpoint_interval=1000,
        compress_output=False,
        resume_from_checkpoint=True
    )

def find_identity_config_path(search_dir: Path) -> Optional[str]:
    """Find IDENTITY_CONFIG.yaml or a prefixed variant in the given directory."""
    candidate = search_dir / "IDENTITY_CONFIG.yaml"
    if candidate.exists():
        return str(candidate)

    matches = sorted(search_dir.glob("*_IDENTITY_CONFIG.yaml"))
    if matches:
        return str(matches[0])

    return None

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Enhanced File Scanner v2.0 - Comprehensive file metadata collection"
    )
    
    parser.add_argument('scan_path', nargs='?', 
                       help='Directory to scan (overrides script configuration)')
    parser.add_argument('-o', '--output-dir', 
                       help='Output directory for results (overrides script configuration)')
    parser.add_argument('-f', '--formats', nargs='+', 
                       choices=['json', 'ndjson', 'csv', 'markdown'],
                       help='Output formats (overrides script configuration)')
    parser.add_argument('--include-hashes', action='store_true',
                       help='Calculate file hashes (overrides script configuration)')
    parser.add_argument('--hash-algorithms', nargs='+',
                       choices=['md5', 'sha1', 'sha256', 'sha512'],
                       help='Hash algorithms to use (overrides script configuration)')
    parser.add_argument('--no-permissions', action='store_true',
                       help='Skip permission information')
    parser.add_argument('--compress', action='store_true',
                       help='Compress output files')
    parser.add_argument('--no-resume', action='store_true',
                       help='Disable resume capability')
    parser.add_argument('--min-size', type=int,
                       help='Minimum file size to process (bytes)')
    parser.add_argument('--max-size', type=int,
                       help='Maximum file size to process (bytes, 0=no limit)')
    parser.add_argument('--exclude', nargs='+',
                       help='Filename patterns to exclude')
    parser.add_argument('--include', nargs='+',
                       help='Filename patterns to include (others excluded)')
    parser.add_argument('--identity-config', type=str,
                       help='Path to IDENTITY_CONFIG.yaml')
    parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    
    args = parser.parse_args()
    
    # Start with user configuration from script constants
    config = create_user_config()
    
    # Override with command line arguments if provided
    if args.scan_path:
        config.scan_path = os.path.abspath(args.scan_path)
    if args.output_dir:
        config.output_dir = args.output_dir
    if args.formats:
        config.output_formats = args.formats
    if args.include_hashes:
        config.include_hashes = True
    if args.hash_algorithms:
        config.hash_algorithms = args.hash_algorithms
    if args.no_permissions:
        config.include_permissions = False
    if args.compress:
        config.compress_output = True
    if args.no_resume:
        config.resume_from_checkpoint = False
    if args.min_size is not None:
        config.min_file_size = args.min_size
    if args.max_size is not None:
        config.max_file_size = args.max_size
    if args.exclude:
        config.exclude_patterns = [p.lower() for p in args.exclude]
    if args.include:
        config.include_patterns = [p.lower() for p in args.include]
    if args.identity_config:
        config.identity_config_path = args.identity_config
    elif IDENTITY_CONFIG_PATH and os.path.exists(IDENTITY_CONFIG_PATH):
        config.identity_config_path = IDENTITY_CONFIG_PATH
    else:
        detected_path = find_identity_config_path(Path(__file__).parent)
        if detected_path:
            config.identity_config_path = detected_path
    
    # Check for psutil if advanced features are needed
    if not PSUTIL_AVAILABLE and (config.include_permissions or config.resume_from_checkpoint):
        print("Warning: psutil not available. Some features may be limited.")
        print("Install with: pip install psutil")
    
    # Create and run scanner
    scanner = EnhancedFileScanner(config)
    
    print(f"Enhanced File Scanner v{VERSION}")
    print("=" * 50)
    print(f"Scanning: {config.scan_path}")
    print(f"Output: {config.output_dir}")
    print(f"Formats: {', '.join(config.output_formats)}")
    print(f"Include Hashes: {config.include_hashes}")
    if config.include_hashes:
        print(f"Hash Algorithms: {', '.join(config.hash_algorithms)}")
    print()
    
    success = scanner.scan()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
