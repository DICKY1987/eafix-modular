"""
Central configuration for DOC_ID system.

Provides:
- Path constants (single source of truth)
- Regex patterns
- Global settings
"""
# DOC_ID: DOC-CONFIG-COMMON-CONFIG-283

import re
from pathlib import Path

# Import from centralized rules module (Phase 1 optimization)
from .rules import DOC_ID_REGEX, DOC_ID_WIDTH

# ============================================================================
# Path Configuration
# ============================================================================

# Calculate module root (SUB_DOC_ID/)
MODULE_ROOT = Path(__file__).parent.parent

# Calculate repository root (ALL_AI/) - go up 3 levels from common/
REPO_ROOT = MODULE_ROOT.parent.parent.parent

# Registry and inventory paths
REGISTRY_PATH = MODULE_ROOT / "5_REGISTRY_DATA" / "DOC_ID_REGISTRY.yaml"
INVENTORY_PATH = MODULE_ROOT / "5_REGISTRY_DATA" / "docs_inventory.jsonl"

# Reports directory
REPORTS_DIR = MODULE_ROOT / "4_REPORTING_MONITORING" / "DOC_ID_reports"

# Ensure reports directory exists
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Patterns and Constants
# ============================================================================

# DEPRECATED: Import DOC_ID_REGEX and DOC_ID_WIDTH from common.rules instead
# Kept here temporarily for backward compatibility (Phase 1 refactoring)
# DOC_ID_REGEX = re.compile(...)  # Now imported from rules.py
# DOC_ID_WIDTH = 4  # Now imported from rules.py

# Eligible file patterns for scanning
ELIGIBLE_PATTERNS = [
    "**/*.py",
    "**/*.yaml",
    "**/*.yml",
    "**/*.json",
    "**/*.ps1",
    "**/*.sh",
    "**/*.md",  # Phase 1: Added for relationship index markdown link detection
]

# Exclude patterns for scanning
EXCLUDE_PATTERNS = [
    ".venv",
    "venv",
    "envs",
    "site-packages",
    "__pycache__",
    ".git",
    "node_modules",
    ".pytest_cache",
    ".worktrees",
    "legacy",
    ".state",
    "refactor_paths.db",
    "*.db-shm",
    "*.db-wal",
    "UTI_Archives",
    "Backups",
    "contracts_by_script",
    "_io_contracts",
]

# ============================================================================
# Settings
# ============================================================================

# Default coverage baseline (set to 100% target for full coverage)
DEFAULT_COVERAGE_BASELINE = 1.00

# Default debounce time for file watcher (seconds)
DEFAULT_DEBOUNCE_SECONDS = 300

# Cache TTL (seconds)
CACHE_TTL_SECONDS = 300
