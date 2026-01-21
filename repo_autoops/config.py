# doc_id: DOC-AUTOOPS-003
"""Configuration management for RepoAutoOps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import structlog
import yaml
from pydantic import BaseModel, Field, ValidationError

from repo_autoops.models.contracts import ModuleContract

__doc_id__ = "DOC-AUTOOPS-003"

logger = structlog.get_logger(__name__)


class WatchConfig(BaseModel):
    enabled: bool = True
    roots: List[Path] = Field(default_factory=lambda: [Path(".")])
    ignore_patterns: List[str] = Field(
        default_factory=lambda: [".git/", "__pycache__/", "*.pyc", ".tmp", ".swp", "~*", "_evidence/", "_quarantine/"]
    )
    file_patterns: List[str] = Field(default_factory=lambda: ["*.py", "*.md", "*.yaml", "*.json"])
    recursive: bool = True
    processing_delay_seconds: int = 2

    class Config:
        arbitrary_types_allowed = True


class GitConfig(BaseModel):
    enabled: bool = True
    commit_batching_enabled: bool = True
    idle_window_seconds: int = 300
    max_files_threshold: int = 20

    class Config:
        arbitrary_types_allowed = True


class SafetyConfig(BaseModel):
    max_actions_per_cycle: int = 100
    dry_run_default: bool = True
    repo_lock_path: Path = Path(".repo_lock")

    class Config:
        arbitrary_types_allowed = True


class Config(BaseModel):
    repository_root: Path = Path(".")
    watch: WatchConfig = Field(default_factory=WatchConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def load_from_file(cls, config_path: Path) -> Config:
        if not config_path.exists():
            logger.warning("config_file_not_found", path=str(config_path))
            return cls()
        try:
            with config_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return cls(**data)
        except (yaml.YAMLError, ValidationError) as e:
            logger.error("config_load_failed", error=str(e))
            raise
