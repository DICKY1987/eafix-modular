"""
Registry Writer Package

doc_id: 2026012321510003
purpose: Single-writer enforcement package
version: 1.0
date: 2026-01-23T21:51:00Z
"""

from services.registry_writer import promotion_patch as _promotion_patch
from services.registry_writer import registry_writer_service as _registry_writer_service

PromotionPatch = _promotion_patch.PromotionPatch
RegistryWriter = _registry_writer_service.RegistryWriter

__all__ = ['PromotionPatch', 'RegistryWriter']
