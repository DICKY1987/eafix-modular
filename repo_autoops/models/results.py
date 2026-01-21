# doc_id: DOC-AUTOOPS-023
"""Result models for operations and validations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

__doc_id__ = "DOC-AUTOOPS-023"


class OperationResult(BaseModel):
    success: bool
    message: str
    output: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    passed: bool
    validator_name: str
    message: str
    details: Optional[Dict[str, Any]] = None
    suggestions: List[str] = Field(default_factory=list)


class ComplianceReport(BaseModel):
    module_id: str
    timestamp: str
    missing_required: List[str] = Field(default_factory=list)
    unexpected_files: List[str] = Field(default_factory=list)
    forbidden_files: List[str] = Field(default_factory=list)
    compliant: bool
