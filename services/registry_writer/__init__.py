"""
Registry Writer Package

doc_id: 2026012322470003
purpose: Single-writer enforcement package
version: 2.0
date: 2026-01-23T22:47:00Z
"""

from services.registry_writer.promotion_patch import (
    PromotionPatch,
    PatchResult,
    PatchOperation,
    PatchOperationType
)

from services.registry_writer.registry_writer_service import (
    RegistryWriterService,
    create_simple_patch
)

__all__ = [
    'PromotionPatch',
    'PatchResult',
    'PatchOperation',
    'PatchOperationType',
    'RegistryWriterService',
    'create_simple_patch'
]
