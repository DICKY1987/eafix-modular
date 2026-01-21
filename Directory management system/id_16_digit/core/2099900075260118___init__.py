"""
Core identity system components for EAFIX.

This package contains the foundational components:
- RegistryStore: Central ID registry with collision prevention
- IDAllocator: ID allocation engine
- FileRenamer: File renaming with git integration
- LifecycleManager: ID lifecycle management
- FrontmatterInjector: Metadata injection for various formats
"""

from .registry_store import RegistryStore, AllocationRecord

__all__ = ['RegistryStore', 'AllocationRecord']
