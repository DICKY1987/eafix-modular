"""
Registry wrapper for DOC_ID_REGISTRY.yaml.

Provides high-level interface for registry operations with caching.
"""
# DOC_ID: DOC-CORE-COMMON-REGISTRY-1171

from pathlib import Path
from typing import Dict, List, Optional

from .config import REGISTRY_PATH
from .utils import load_yaml, save_yaml
from .errors import (
    RegistryNotFoundError,
    CategoryNotFoundError,
    DuplicateDocIDError,
)
from .cache import FileCache


class Registry:
    """
    Singleton wrapper for DOC_ID_REGISTRY.yaml.
    
    Provides cached access to registry with helper methods.
    Uses file-based caching for automatic invalidation.
    """
    
    _instance: Optional['Registry'] = None
    _data: Optional[Dict] = None
    _cache: FileCache = FileCache(ttl=600)  # 10 minutes
    
    def __init__(self, registry_path: Path = REGISTRY_PATH):
        """
        Initialize registry wrapper.
        
        Args:
            registry_path: Path to registry file (default: from config)
        """
        self.registry_path = registry_path
    
    @classmethod
    def get_instance(cls, registry_path: Path = REGISTRY_PATH) -> 'Registry':
        """
        Get singleton instance.
        
        Args:
            registry_path: Path to registry file
            
        Returns:
            Registry instance
        """
        if cls._instance is None:
            cls._instance = cls(registry_path)
        return cls._instance
    
    def load(self) -> Dict:
        """
        Load registry (cached with file modification tracking).
        
        Returns:
            Registry data dictionary
            
        Raises:
            RegistryNotFoundError: If file doesn't exist
        """
        # Try cache first
        cached_data = self._cache.get_file(self.registry_path)
        if cached_data is not None:
            self._data = cached_data
            return self._data
        
        # Load from file and cache
        self._data = load_yaml(self.registry_path)
        self._cache.set_file(self.registry_path, self._data)
        return self._data
    
    def reload(self) -> Dict:
        """
        Force reload from disk (clears cache).
        
        Returns:
            Fresh registry data
        """
        self._data = None
        self._cache.invalidate(str(self.registry_path))
        return self.load()
    
    def save(self, data: Optional[Dict] = None) -> None:
        """
        Save registry and update cache.
        
        Args:
            data: Registry data to save (uses cached if None)
        """
        if data is None:
            data = self._data
        
        if data is None:
            raise ValueError("No data to save")
        
        save_yaml(self.registry_path, data)
        self._data = data
        # Update cache with new data
        self._cache.set_file(self.registry_path, data)
    
    # ========================================================================
    # Category Methods
    # ========================================================================
    
    def get_categories(self) -> Dict[str, Dict]:
        """Get all categories."""
        return self.load().get('categories', {})
    
    def get_category(self, name: str) -> Dict:
        """
        Get category by name.
        
        Args:
            name: Category name (lowercase, e.g., "core")
            
        Returns:
            Category data dictionary
            
        Raises:
            CategoryNotFoundError: If category doesn't exist
        """
        categories = self.get_categories()
        if name not in categories:
            raise CategoryNotFoundError(name)
        return categories[name]
    
    def get_category_prefix(self, name: str) -> str:
        """Get category prefix (e.g., "CORE")."""
        return self.get_category(name).get('prefix', name.upper())
    
    def get_next_id(self, category: str) -> int:
        """Get next available ID number for category."""
        return self.get_category(category).get('next_id', 1)
    
    def increment_next_id(self, category: str) -> int:
        """
        Increment and return next ID for category.
        
        Args:
            category: Category name
            
        Returns:
            The incremented ID number
        """
        data = self.load()
        cat = data['categories'][category]
        next_id = cat.get('next_id', 1)
        cat['next_id'] = next_id + 1
        cat['count'] = cat.get('count', 0) + 1
        self._data = data
        return next_id
    
    # ========================================================================
    # Doc Methods
    # ========================================================================
    
    def get_docs(self) -> List[Dict]:
        """Get all doc entries."""
        return self.load().get('docs', [])
    
    def get_doc(self, doc_id: str) -> Optional[Dict]:
        """
        Get doc entry by ID.
        
        Args:
            doc_id: Doc ID to find
            
        Returns:
            Doc entry dictionary or None if not found
        """
        for doc in self.get_docs():
            if doc.get('doc_id') == doc_id:
                return doc
        return None
    
    def doc_id_exists(self, doc_id: str) -> bool:
        """Check if doc_id exists in registry."""
        return self.get_doc(doc_id) is not None
    
    def add_doc(self, doc: Dict) -> None:
        """
        Add new doc entry to registry.
        
        Args:
            doc: Doc entry dictionary
            
        Raises:
            DuplicateDocIDError: If doc_id already exists
        """
        doc_id = doc.get('doc_id')
        if not doc_id:
            raise ValueError("Doc entry must have 'doc_id' field")
        
        if self.doc_id_exists(doc_id):
            raise DuplicateDocIDError(doc_id)
        
        data = self.load()
        data.setdefault('docs', []).append(doc)
        self._data = data
    
    # ========================================================================
    # Metadata Methods
    # ========================================================================
    
    def get_metadata(self) -> Dict:
        """Get registry metadata."""
        return self.load().get('metadata', {})
    
    def get_total_docs(self) -> int:
        """Get total number of docs."""
        return len(self.get_docs())
    
    def update_metadata(self, **kwargs) -> None:
        """
        Update metadata fields.
        
        Args:
            **kwargs: Metadata fields to update
        """
        data = self.load()
        metadata = data.setdefault('metadata', {})
        metadata.update(kwargs)
        self._data = data
