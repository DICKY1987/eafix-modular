# DOC_ID: DOC-LEGACY-0014
"""
Reentry Helpers
---------------
Hybrid ID serializer/validator and Indicator JSON Schema validator.

- reentry_helpers.vocab: Load canonical vocab (duration/proximity/outcome/direction/generation)
- reentry_helpers.hybrid_id: Compose/parse/validate reentry keys and comment suffixes
- reentry_helpers.indicator_validator: Validate indicator records against JSON Schema

Minimal, stdlib-only; will use `jsonschema` if available for stricter validation.
"""
__all__ = ["vocab", "hybrid_id", "indicator_validator"]
