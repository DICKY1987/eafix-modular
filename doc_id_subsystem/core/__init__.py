"""
Common utilities for DOC_ID system.

Provides shared configuration, utilities, and helpers to eliminate
code duplication across the DOC_ID management tools.

Version: 2.1.0
"""
# DOC_ID: DOC-CORE-COMMON-INIT-1173

__version__ = "2.1.0"

from .config import (
    REPO_ROOT,
    MODULE_ROOT,
    REGISTRY_PATH,
    INVENTORY_PATH,
    REPORTS_DIR,
    DOC_ID_REGEX,
    ELIGIBLE_PATTERNS,
    EXCLUDE_PATTERNS,
)

from .utils import (
    load_yaml,
    save_yaml,
    load_jsonl,
    save_jsonl,
    validate_doc_id,
    extract_category_from_doc_id,
)

from .errors import (
    DocIDError,
    RegistryNotFoundError,
    InventoryNotFoundError,
    InvalidDocIDError,
)

from .logging_setup import (
    setup_logging,
    get_logger,
)

from .cache import (
    SimpleCache,
    FileCache,
    cached,
    get_cache,
)

__all__ = [
    # Config
    'REPO_ROOT',
    'MODULE_ROOT',
    'REGISTRY_PATH',
    'INVENTORY_PATH',
    'REPORTS_DIR',
    'DOC_ID_REGEX',
    'ELIGIBLE_PATTERNS',
    'EXCLUDE_PATTERNS',
    # Utils
    'load_yaml',
    'save_yaml',
    'load_jsonl',
    'save_jsonl',
    'validate_doc_id',
    'extract_category_from_doc_id',
    # Errors
    'DocIDError',
    'RegistryNotFoundError',
    'InventoryNotFoundError',
    'InvalidDocIDError',
    # Logging
    'setup_logging',
    'get_logger',
    # Caching
    'SimpleCache',
    'FileCache',
    'cached',
    'get_cache',
]
