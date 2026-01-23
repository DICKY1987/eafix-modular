"""
Automation Descriptor Subsystem

doc_id: DOC-AUTO-DESC-0001
purpose: Package initialization for automation_descriptor subsystem
phase: Phase 1 - Architecture
version: 1.0.0
"""

__version__ = "1.0.0"
__doc_id__ = "DOC-AUTO-DESC-0001"

# Component imports (will be populated as components are implemented)
# Phase 2: Infrastructure
# from .work_queue import WorkQueue
# from .lock_manager import LockManager
# from .suppression_manager import SuppressionManager
# from .stability_checker import StabilityChecker
# from .audit_logger import AuditLogger

# Phase 3: ID & Rename
# from .id_allocator import IDAllocator
# from .file_renamer import FileRenamer
# from .classifier import Classifier

# Phase 4: Parser & Descriptor
# from .descriptor_extractor import DescriptorExtractor

# Phase 5: Registry Writer
# from .registry_writer_service import RegistryWriterService
# from .write_policy_validator import WritePolicyValidator
# from .normalizer import Normalizer
# from .backup_manager import BackupManager

# Phase 6: Watcher
# from .watcher_daemon import WatcherDaemon
# from .event_handlers import EventHandlers

# Phase 7: Reconciliation
# from .reconciler import Reconciler
# from .reconcile_scheduler import ReconcileScheduler

# Phase 8: CLI
# from .cli import main

__all__ = [
    "__version__",
    "__doc_id__",
    # Components will be added here as they're implemented
]
