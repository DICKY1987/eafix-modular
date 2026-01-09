#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DOC_ID: DOC-SERVICE-0127
# TRIGGER_ID: TRIGGER-WATCHER-FILE-WATCHER-001
# DOC_LINK: DOC-SCRIPT-DOC-ID-FILE-WATCHER-009
"""
DOC_ID File Watcher - Automatic Scan Trigger with Smart Category Detection

ENHANCEMENT: Now auto-assigns doc_ids across ALL 47 repository directories
using intelligent path-based category detection.

PATTERN: EXEC-003 Tool Availability Guards
Ground Truth: Watcher process running, scan triggered on changes, doc_ids auto-assigned everywhere

USAGE:
    python file_watcher.py
    python file_watcher.py --debounce 600
"""

import argparse
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# PATTERN: Tool availability guard
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("❌ watchdog not installed")
    print("Run: pip install watchdog")
    sys.exit(1)

# Add parent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT, MODULE_ROOT

SCANNER_SCRIPT = MODULE_ROOT / "1_CORE_OPERATIONS" / "doc_id_scanner.py"
ASSIGNER_SCRIPT = MODULE_ROOT / "1_CORE_OPERATIONS" / "doc_id_assigner.py"
ELIGIBLE_EXTENSIONS = {'.py', '.md', '.yaml', '.yml', '.json', '.ps1', '.sh', '.txt'}
EXCLUDE_DIRS = {'.git', '__pycache__', '.venv', 'node_modules', '.pytest_cache', 
                'UTI_Archives', 'Backups', '.acms_runs', 'envs'}

# ENHANCEMENT: Expanded monitoring configuration for top directories
MONITORED_FOLDERS = {
    # Original 3 (backward compatibility)
    'glossary': {
        'path': REPO_ROOT / 'SUB_GLOSSARY',
        'patterns': ['.yaml', '.yml', '.md', '.py'],
        'category': 'glossary',
        'exclude': ['config', '__pycache__', '.glossary-metadata.yaml']
    },
    'process_schemas': {
        'path': REPO_ROOT / 'PROCESS_STEP_LIB' / 'schemas' / 'source',
        'patterns': ['.yaml', '.yml'],
        'category': 'spec',
        'exclude': []
    },
    'process_tools': {
        'path': REPO_ROOT / 'PROCESS_STEP_LIB' / 'tools',
        'patterns': ['.py'],
        'category': 'script',
        'exclude': ['__pycache__', '__init__.py']
    },
    
    # NEW: Top 15 directories by file count
    'runtime': {
        'path': REPO_ROOT / 'RUNTIME',
        'patterns': ['.py', '.yaml', '.yml', '.md', '.json'],
        'category': 'runtime',
        'exclude': ['__pycache__']
    },
    'governance': {
        'path': REPO_ROOT / 'GOVERNANCE',
        'patterns': ['.md', '.yaml', '.yml', '.json'],
        'category': 'policy',
        'exclude': []
    },
    'context': {
        'path': REPO_ROOT / 'CONTEXT',
        'patterns': ['.md', '.yaml', '.yml', '.json'],
        'category': 'guide',
        'exclude': []
    },
    'scripts': {
        'path': REPO_ROOT / 'scripts',
        'patterns': ['.py', '.ps1', '.sh'],
        'category': 'script',
        'exclude': ['__pycache__']
    },
    'tests': {
        'path': REPO_ROOT / 'tests',
        'patterns': ['.py'],
        'category': 'test',
        'exclude': ['__pycache__', '__init__.py']
    },
    'uti_tools': {
        'path': REPO_ROOT / 'UTI_TOOLS',
        'patterns': ['.py', '.ps1'],
        'category': 'script',
        'exclude': ['__pycache__']
    },
    'automation': {
        'path': REPO_ROOT / 'automation',
        'patterns': ['.py'],
        'category': 'script',
        'exclude': ['__pycache__', '__init__.py']
    },
    'modules': {
        'path': REPO_ROOT / 'modules',
        'patterns': ['.py'],
        'category': 'module',
        'exclude': ['__pycache__', '__init__.py']
    },
    'docs': {
        'path': REPO_ROOT / 'docs',
        'patterns': ['.md', '.yaml', '.yml'],
        'category': 'guide',
        'exclude': []
    },
    'contracts': {
        'path': REPO_ROOT / 'CONTRACTS',
        'patterns': ['.md', '.yaml', '.yml', '.json'],
        'category': 'contract',
        'exclude': []
    },
    'workflows': {
        'path': REPO_ROOT / 'WORKFLOWS',
        'patterns': ['.yaml', '.yml', '.json', '.md'],
        'category': 'workflow',
        'exclude': []
    },
    'config': {
        'path': REPO_ROOT / 'config',
        'patterns': ['.yaml', '.yml', '.json'],
        'category': 'config',
        'exclude': []
    },
    'data': {
        'path': REPO_ROOT / 'data',
        'patterns': ['.json', '.yaml', '.yml'],
        'category': 'data',
        'exclude': []
    },
    'specs': {
        'path': REPO_ROOT / 'specs',
        'patterns': ['.yaml', '.yml', '.md'],
        'category': 'spec',
        'exclude': []
    },
    'benchmarks': {
        'path': REPO_ROOT / 'benchmarks',
        'patterns': ['.py', '.yaml', '.yml'],
        'category': 'benchmark',
        'exclude': ['__pycache__']
    },
}


def smart_category_detection(path: Path) -> str:
    """
    ENHANCEMENT: Intelligent category detection based on path patterns.
    
    Uses multi-layer heuristics:
    1. Path pattern matching (substring checks)
    2. Directory name analysis
    3. File extension fallback
    4. Default to 'general'
    
    Args:
        path: Path object of the file
        
    Returns:
        Category string (e.g., 'test', 'script', 'guide', 'general')
    """
    try:
        path_str = str(path.relative_to(REPO_ROOT)).lower().replace('\\', '/')
    except ValueError:
        # Path not under REPO_ROOT
        return 'general'
    
    # Pattern matching: path contains keyword
    pattern_map = {
        'test': ['test', '/tests/', 'test_', '_test.'],
        'script': ['script', '/scripts/', '/automation/'],
        'guide': ['/docs/', '/doc/', 'documentation', 'readme', 'guide'],
        'policy': ['governance', 'policy', 'policies'],
        'spec': ['/spec/', '/specs/', 'schema', 'schemas'],
        'runtime': ['/runtime/'],
        'workflow': ['workflow', '/workflows/'],
        'config': ['/config/', 'configuration'],
        'contract': ['contract', '/contracts/'],
        'module': ['/modules/', '/module/'],
        'data': ['/data/'],
        'benchmark': ['benchmark', '/benchmarks/'],
        'report': ['/report/', '/reports/'],
        'template': ['/template/', '/templates/'],
        'prompt': ['/prompt/', '/prompts/'],
    }
    
    # Check patterns
    for category, patterns in pattern_map.items():
        if any(pattern in path_str for pattern in patterns):
            return category
    
    # Directory name heuristics
    parts = path.parts
    if len(parts) > 1:
        parent_dir = parts[-2].lower()
        if 'test' in parent_dir:
            return 'test'
        elif 'script' in parent_dir:
            return 'script'
        elif 'doc' in parent_dir:
            return 'guide'
    
    # File extension fallback
    ext = path.suffix.lower()
    if ext == '.py':
        return 'script'
    elif ext in ['.md', '.txt']:
        return 'guide'
    elif ext in ['.yaml', '.yml', '.json']:
        return 'config'
    elif ext in ['.ps1', '.sh']:
        return 'script'
    
    # Default
    return 'general'


class DocIDEventHandler(FileSystemEventHandler):
    """Handle file system events for DOC_ID scanning"""
    
    def __init__(self, debounce_seconds=300):
        self.last_scan = datetime.min
        self.debounce = timedelta(seconds=debounce_seconds)
        self.pending_scan = False
        self.modified_files = set()
        self.stats = {
            'files_detected': 0,
            'doc_ids_assigned': 0,
            'explicit_matches': 0,
            'smart_detections': 0,
            'scan_triggers': 0
        }
    
    def should_process(self, path: Path) -> bool:
        """Check if file should trigger scan"""
        # Skip directories
        if path.is_dir():
            return False
        
        # Check extension
        if path.suffix not in ELIGIBLE_EXTENSIONS:
            return False
        
        # Check excluded directories
        if any(excluded in path.parts for excluded in EXCLUDE_DIRS):
            return False
        
        return True
    
    def get_folder_category(self, path: Path):
        """
        ENHANCEMENT: Determine doc_id category using explicit mapping + smart detection.
        
        First tries MONITORED_FOLDERS explicit mapping.
        Falls back to smart_category_detection() for unmapped paths.
        """
        try:
            # Try explicit mapping first
            for folder_name, folder_config in MONITORED_FOLDERS.items():
                folder_path = folder_config['path']
                if not folder_path.exists():
                    continue
                
                # Check if file is under this folder
                try:
                    rel_path = path.relative_to(folder_path)
                    
                    # Check file extension matches patterns
                    if path.suffix not in folder_config['patterns']:
                        continue
                    
                    # Check exclusions
                    if any(excl in str(rel_path) for excl in folder_config['exclude']):
                        continue
                    
                    self.stats['explicit_matches'] += 1
                    return folder_config['category']
                except ValueError:
                    # Not relative to this folder
                    continue
            
            # ENHANCEMENT: Fall back to smart detection
            category = smart_category_detection(path)
            if category:
                self.stats['smart_detections'] += 1
                return category
                
        except Exception as e:
            print(f"⚠️  Error determining category for {path}: {e}")
        
        return 'general'  # Safe fallback
    
    def has_doc_id(self, file_path: Path) -> bool:
        """Check if file already has a doc_id."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            return bool(re.search(r'DOC-[A-Z]+-[A-Z0-9-]+-[0-9]+', content))
        except Exception:
            return False
    
    def on_modified(self, event):
        """Trigger scan on file modification"""
        if event.is_directory:
            return
        
        path = Path(event.src_path)
        
        if not self.should_process(path):
            return
        
        # Track modified file
        self.modified_files.add(str(path.relative_to(REPO_ROOT)))
        self.stats['files_detected'] += 1
        
        # Debounce
        now = datetime.now()
        if now - self.last_scan < self.debounce:
            self.pending_scan = True
            return
        
        # Trigger scan
        self.trigger_scan()
    
    def on_created(self, event):
        """Handle new files"""
        self.on_modified(event)
    
    def trigger_scan(self):
        """Execute scanner and assign doc_ids to new files"""
        if not self.modified_files:
            return
        
        print(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] Files changed: {len(self.modified_files)}")
        self.stats['scan_triggers'] += 1
        
        # ENHANCEMENT: Check ALL files for doc_id assignment (not just special folders)
        files_by_category = {}
        for file_str in self.modified_files:
            file_path = REPO_ROOT / file_str
            if not file_path.exists():
                continue
            
            # Get category (explicit or smart)
            category = self.get_folder_category(file_path)
            if category:
                files_by_category.setdefault(category, []).append(file_path)
        
        # Assign doc_ids by category
        if files_by_category:
            total_files = sum(len(files) for files in files_by_category.values())
            print(f"\n🔍 Checking {total_files} files across {len(files_by_category)} categories for doc_ids...")
            
            for category, files in files_by_category.items():
                print(f"\n   Category: {category}")
                for file_path in files:
                    # Check if file already has doc_id
                    if self.has_doc_id(file_path):
                        continue
                    
                    print(f"  📝 Assigning doc_id to {file_path.relative_to(REPO_ROOT)}...")
                    
                    # Invoke assigner in single mode
                    result = subprocess.run(
                        [sys.executable, str(ASSIGNER_SCRIPT), 
                         'single', '--file', str(file_path), '--category', category],
                        capture_output=True,
                        text=True,
                        cwd=REPO_ROOT,
                        timeout=60
                    )
                    
                    if result.returncode == 0:
                        self.stats['doc_ids_assigned'] += 1
                        # Extract doc_id from output
                        for line in result.stdout.split('\n'):
                            if 'DOC-' in line:
                                print(f"     ✅ {line.strip()}")
                                break
                    else:
                        print(f"     ❌ Assignment failed: {result.stderr[:100]}")
        
        # Now run scanner
        print(f"\n📊 Triggering scan...")
        
        result = subprocess.run(
            [sys.executable, str(SCANNER_SCRIPT), 'scan'],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✅ Scan completed successfully")
            # Parse and display coverage
            if 'Coverage:' in result.stdout:
                for line in result.stdout.split('\n'):
                    if 'Coverage:' in line or 'Scanned:' in line:
                        print(f"   {line.strip()}")
        else:
            print(f"❌ Scan failed (exit code: {result.returncode})")
            if result.stderr:
                print(f"Error: {result.stderr[:200]}")
        
        # Display stats
        print(f"\n📈 Session Stats:")
        print(f"   Files detected: {self.stats['files_detected']}")
        print(f"   Doc IDs assigned: {self.stats['doc_ids_assigned']}")
        print(f"   Explicit matches: {self.stats['explicit_matches']}")
        print(f"   Smart detections: {self.stats['smart_detections']}")
        print(f"   Scan triggers: {self.stats['scan_triggers']}")
        
        self.last_scan = datetime.now()
        self.modified_files.clear()
        self.pending_scan = False


def main():
    parser = argparse.ArgumentParser(description="DOC_ID File Watcher with Smart Category Detection")
    parser.add_argument('--debounce', type=int, default=300,
                       help='Debounce interval in seconds (default: 300)')
    args = parser.parse_args()
    
    print("═══════════════════════════════════════════════════════════════")
    print("   DOC_ID FILE WATCHER - ENHANCED")
    print("═══════════════════════════════════════════════════════════════")
    print(f"Watching: {REPO_ROOT}")
    print(f"Scanner: {SCANNER_SCRIPT}")
    print(f"Debounce: {args.debounce} seconds")
    print(f"Monitored folders: {len(MONITORED_FOLDERS)} explicit + smart detection")
    print(f"Enhancement: Auto-assigns doc_ids across ALL directories")
    print("Press Ctrl+C to stop")
    print("═══════════════════════════════════════════════════════════════\n")
    
    # Verify scanner exists
    if not SCANNER_SCRIPT.exists():
        print(f"❌ Scanner not found: {SCANNER_SCRIPT}")
        sys.exit(1)
    
    # Verify assigner exists
    if not ASSIGNER_SCRIPT.exists():
        print(f"❌ Assigner not found: {ASSIGNER_SCRIPT}")
        sys.exit(1)
    
    # Create handler and observer
    handler = DocIDEventHandler(debounce_seconds=args.debounce)
    observer = Observer()
    observer.schedule(handler, str(REPO_ROOT), recursive=True)
    observer.start()
    
    print("✅ Watcher started - monitoring for changes across all directories...\n")
    
    try:
        while True:
            time.sleep(1)
            # Check for pending scans
            if handler.pending_scan:
                now = datetime.now()
                if now - handler.last_scan >= handler.debounce:
                    handler.trigger_scan()
    except KeyboardInterrupt:
        print("\n\nStopping watcher...")
        observer.stop()
    
    observer.join()
    print("✅ Watcher stopped")
    
    # Final stats
    print("\n" + "="*60)
    print("FINAL SESSION STATS:")
    print("="*60)
    for key, value in handler.stats.items():
        print(f"  {key}: {value}")
    print("="*60)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
