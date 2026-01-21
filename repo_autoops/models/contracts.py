# doc_id: DOC-AUTOOPS-022
"""Module contract models for policy enforcement."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

__doc_id__ = "DOC-AUTOOPS-022"


class ValidationRule(BaseModel):
    name: str
    enabled: bool = True
    threshold: Optional[int] = None


class ModuleContract(BaseModel):
    module_id: str
    root: Path
    description: str = ""
    canonical_allowlist: List[str] = Field(default_factory=list)
    required_paths: List[str] = Field(default_factory=list)
    optional_paths: List[str] = Field(default_factory=list)
    generated_patterns: List[str] = Field(default_factory=list)
    run_artifact_patterns: List[str] = Field(default_factory=list)
    forbidden_patterns: List[str] = Field(default_factory=list)
    quarantine_path: Path = Path("_quarantine")
    validation_rules: List[ValidationRule] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


class FileClassification(BaseModel):
    classification: str
    reason: str
    matched_pattern: Optional[str] = None
    suggested_action: Optional[str] = None
