#!/usr/bin/env python3
"""
doc_id: 2026012322470016
Generator Orchestrator - Stale Detection and Rebuild

Tracks generator outputs and triggers rebuilds when source registry changes.
Prevents infinite loops by excluding generator records from hash computation.
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class GeneratorOrchestrator:
    """
    Manages generator lifecycle: detect staleness, trigger rebuilds.
    
    Strategy:
    1. Compute registry hash (excluding generator records)
    2. Compare with last known hash for each generator
    3. Mark stale generators
    4. Trigger rebuild (via work queue or direct call)
    5. Update generator metadata with new hash
    """
    
    def __init__(self, registry_path: Path):
        """
        Initialize generator orchestrator.
        
        Args:
            registry_path: Path to UNIFIED_SSOT_REGISTRY.json
        """
        self.registry_path = Path(registry_path)
        self.generators: Dict[str, Dict[str, Any]] = {}
    
    def load_generators(self):
        """Load generator records from registry."""
        if not self.registry_path.exists():
            logger.warning(f"Registry does not exist: {self.registry_path}")
            return
        
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            for record in registry.get("records", []):
                if record.get("record_kind") == "generator":
                    gen_id = record.get("generator_id")
                    if gen_id:
                        self.generators[gen_id] = record
            
            logger.info(f"Loaded {len(self.generators)} generators")
        
        except Exception as e:
            logger.error(f"Error loading generators: {e}")
    
    def compute_source_hash(self) -> str:
        """
        Compute hash of source records (exclude generators).
        
        This prevents infinite rebuild loops.
        
        Returns:
            SHA-256 hash of non-generator records
        """
        if not self.registry_path.exists():
            return "0" * 64
        
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            # Filter out generator records
            source_records = [
                r for r in registry.get("records", [])
                if r.get("record_kind") != "generator"
            ]
            
            # Compute hash of source records only
            records_json = json.dumps(source_records, sort_keys=True)
            return hashlib.sha256(records_json.encode('utf-8')).hexdigest()
        
        except Exception as e:
            logger.error(f"Error computing source hash: {e}")
            return "0" * 64
    
    def detect_stale_generators(self) -> List[str]:
        """
        Detect generators that need rebuild.
        
        Returns:
            List of stale generator IDs
        """
        current_hash = self.compute_source_hash()
        stale = []
        
        for gen_id, generator in self.generators.items():
            last_source_hash = generator.get("last_source_hash", "")
            
            if last_source_hash != current_hash:
                stale.append(gen_id)
                logger.info(f"Generator {gen_id} is stale (hash mismatch)")
        
        return stale
    
    def mark_generator_rebuilt(self, gen_id: str):
        """
        Mark generator as rebuilt with current source hash.
        
        Args:
            gen_id: Generator ID
        """
        if gen_id not in self.generators:
            logger.warning(f"Generator not found: {gen_id}")
            return
        
        current_hash = self.compute_source_hash()
        
        # Update generator record (in-memory)
        self.generators[gen_id]["last_source_hash"] = current_hash
        self.generators[gen_id]["last_rebuilt_utc"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Marked generator {gen_id} as rebuilt")
        
        # Note: Actual registry update would go through RegistryWriter
    
    def get_generator_status(self) -> Dict[str, Any]:
        """Get status of all generators."""
        current_hash = self.compute_source_hash()
        
        status = {
            "total_generators": len(self.generators),
            "current_source_hash": current_hash[:16],
            "generators": []
        }
        
        for gen_id, generator in self.generators.items():
            last_hash = generator.get("last_source_hash", "")
            is_stale = (last_hash != current_hash)
            
            status["generators"].append({
                "generator_id": gen_id,
                "is_stale": is_stale,
                "last_rebuilt": generator.get("last_rebuilt_utc", "never")
            })
        
        return status
