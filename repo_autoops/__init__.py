# doc_id: DOC-AUTOOPS-001
"""
RepoAutoOps - Automated Git operations with file watching and policy enforcement.

This package provides a zero-touch Git automation system that:
- Watches filesystem for changes
- Enforces module contracts and allowlists
- Assigns identity (16-digit prefix + doc_id)
- Validates files before committing
- Handles conflicts via quarantine
- Provides comprehensive audit logging
"""

__version__ = "0.1.0"
__doc_id__ = "DOC-AUTOOPS-001"

# Avoid circular imports by using TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from repo_autoops.config import Config
    from repo_autoops.orchestrator import Orchestrator

__all__ = ["__version__"]
