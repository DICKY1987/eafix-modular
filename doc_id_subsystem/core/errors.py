"""
Custom exceptions for DOC_ID system.

Provides hierarchical exception structure for better error handling.
"""
# DOC_ID: DOC-CORE-COMMON-ERRORS-1169


class DocIDError(Exception):
    """Base exception for DOC_ID system."""
    pass


class RegistryNotFoundError(DocIDError):
    """Registry file not found."""
    
    def __init__(self, path=None):
        self.path = path
        msg = f"Registry file not found: {path}" if path else "Registry file not found"
        super().__init__(msg)


class InventoryNotFoundError(DocIDError):
    """Inventory file not found."""
    
    def __init__(self, path=None):
        self.path = path
        msg = f"Inventory file not found: {path}" if path else "Inventory file not found"
        super().__init__(msg)


class InvalidDocIDError(DocIDError):
    """Doc ID format is invalid."""
    
    def __init__(self, doc_id=None):
        self.doc_id = doc_id
        msg = f"Invalid doc_id format: {doc_id}" if doc_id else "Invalid doc_id format"
        super().__init__(msg)


class DuplicateDocIDError(DocIDError):
    """Duplicate doc_id found."""
    
    def __init__(self, doc_id=None, paths=None):
        self.doc_id = doc_id
        self.paths = paths or []
        msg = f"Duplicate doc_id: {doc_id}"
        if paths:
            msg += f" (found in {len(paths)} files)"
        super().__init__(msg)


class CategoryNotFoundError(DocIDError):
    """Category not found in registry."""
    
    def __init__(self, category=None):
        self.category = category
        msg = f"Category not found: {category}" if category else "Category not found"
        super().__init__(msg)


class RegistryCorruptedError(DocIDError):
    """Registry file is corrupted or invalid."""
    
    def __init__(self, reason=None):
        self.reason = reason
        msg = f"Registry corrupted: {reason}" if reason else "Registry file corrupted"
        super().__init__(msg)
