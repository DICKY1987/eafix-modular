# doc_id: DOC-SERVICE-0197
# DOC_ID: DOC-SERVICE-0107
"""
Re-entry Vocabulary Management

Provides canonical vocabulary definitions for hybrid ID components.
Ensures consistency across Python and MQL4 implementations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ReentryVocabulary:
    """Manages canonical re-entry vocabulary from JSON specification."""
    
    def __init__(self, vocab_file: Optional[Path] = None):
        """Initialize vocabulary from JSON file."""
        if vocab_file is None:
            vocab_file = Path(__file__).parent / "reentry_vocab.json"
        
        self.vocab_file = Path(vocab_file)
        self.vocab_data: Dict[str, Any] = {}
        self.load_vocabulary()
    
    def load_vocabulary(self) -> None:
        """Load vocabulary from JSON file."""
        try:
            with open(self.vocab_file, 'r') as f:
                self.vocab_data = json.load(f)
            logger.debug(f"Loaded vocabulary from {self.vocab_file}")
        except Exception as e:
            logger.error(f"Failed to load vocabulary: {e}")
            self.vocab_data = self._get_default_vocabulary()
    
    def _get_default_vocabulary(self) -> Dict[str, Any]:
        """Provide default vocabulary if file loading fails."""
        return {
            "duration_buckets": [
                {"token": "FLASH", "max_minutes": 5, "iso_limit": "PT5M", "desc": "Very short burst; <= 5 minutes"},
                {"token": "QUICK", "max_minutes": 30, "iso_limit": "PT30M", "desc": "Short move; <= 30 minutes"},
                {"token": "LONG", "max_minutes": 240, "iso_limit": "PT4H", "desc": "Sustained move; <= 4 hours"},
                {"token": "EXTENDED", "max_minutes": None, "iso_limit": None, "desc": "Prolonged; > 4 hours"}
            ],
            "proximity_buckets": [
                {"token": "PRE_1H", "window_minutes": [-60, 0], "desc": "Pre-event window"},
                {"token": "AT_EVENT", "window_minutes": [0, 5], "desc": "At event window"},
                {"token": "POST_30M", "window_minutes": [1, 30], "desc": "Post-event window"}
            ],
            "outcome_buckets": [
                {"token": "W2", "rank": 2, "desc": "Strong win"},
                {"token": "W1", "rank": 1, "desc": "Win"},
                {"token": "BE", "rank": 0, "desc": "Break-even"},
                {"token": "L1", "rank": -1, "desc": "Loss"},
                {"token": "L2", "rank": -2, "desc": "Strong loss"}
            ],
            "direction_enum": ["LONG", "SHORT", "ANY"],
            "generation_range": {"min": 1, "max": 3},
            "strength_range": {"min": 0.0, "max": 1.0}
        }
    
    def get_duration_tokens(self) -> List[str]:
        """Get all valid duration tokens."""
        return [bucket["token"] for bucket in self.vocab_data.get("duration_buckets", [])]
    
    def get_proximity_tokens(self) -> List[str]:
        """Get all valid proximity tokens."""
        return [bucket["token"] for bucket in self.vocab_data.get("proximity_buckets", [])]
    
    def get_outcome_tokens(self) -> List[str]:
        """Get all valid outcome tokens."""
        return [bucket["token"] for bucket in self.vocab_data.get("outcome_buckets", [])]
    
    def get_direction_tokens(self) -> List[str]:
        """Get all valid direction tokens."""
        return self.vocab_data.get("direction_enum", ["LONG", "SHORT", "ANY"])
    
    def get_generation_range(self) -> tuple[int, int]:
        """Get valid generation range (min, max)."""
        gen_range = self.vocab_data.get("generation_range", {"min": 1, "max": 3})
        return gen_range["min"], gen_range["max"]
    
    def get_strength_range(self) -> tuple[float, float]:
        """Get valid strength range (min, max)."""
        str_range = self.vocab_data.get("strength_range", {"min": 0.0, "max": 1.0})
        return str_range["min"], str_range["max"]
    
    def validate_duration(self, duration: str) -> bool:
        """Validate duration token."""
        return duration in self.get_duration_tokens()
    
    def validate_proximity(self, proximity: str) -> bool:
        """Validate proximity token."""
        return proximity in self.get_proximity_tokens()
    
    def validate_outcome(self, outcome: str) -> bool:
        """Validate outcome token."""
        return outcome in self.get_outcome_tokens()
    
    def validate_direction(self, direction: str) -> bool:
        """Validate direction token."""
        return direction in self.get_direction_tokens()
    
    def validate_generation(self, generation: int) -> bool:
        """Validate generation value."""
        min_gen, max_gen = self.get_generation_range()
        return min_gen <= generation <= max_gen
    
    def validate_calendar(self, calendar: str) -> bool:
        """Validate calendar identifier format."""
        if calendar == "NONE":
            return True
        elif calendar.startswith("CAL8_") and len(calendar) >= 8:
            return True
        elif calendar.startswith("CAL5_") and len(calendar) >= 8:
            return True
        else:
            return False
    
    def get_duration_max_minutes(self, duration: str) -> Optional[int]:
        """Get maximum minutes for a duration token."""
        for bucket in self.vocab_data.get("duration_buckets", []):
            if bucket["token"] == duration:
                return bucket["max_minutes"]
        return None
    
    def get_outcome_rank(self, outcome: str) -> Optional[int]:
        """Get numerical rank for an outcome token."""
        for bucket in self.vocab_data.get("outcome_buckets", []):
            if bucket["token"] == outcome:
                return bucket["rank"]
        return None
    
    def get_proximity_window(self, proximity: str) -> Optional[List[int]]:
        """Get time window for a proximity token."""
        for bucket in self.vocab_data.get("proximity_buckets", []):
            if bucket["token"] == proximity:
                return bucket["window_minutes"]
        return None
    
    def get_all_valid_tokens(self) -> Dict[str, List[str]]:
        """Get all valid tokens organized by category."""
        return {
            "duration": self.get_duration_tokens(),
            "proximity": self.get_proximity_tokens(), 
            "outcome": self.get_outcome_tokens(),
            "direction": self.get_direction_tokens()
        }
    
    def is_valid_hybrid_context(self, outcome: str, duration: str, proximity: str, 
                              calendar: str, direction: str, generation: int) -> tuple[bool, List[str]]:
        """Validate complete hybrid ID context."""
        errors = []
        
        if not self.validate_outcome(outcome):
            errors.append(f"Invalid outcome: {outcome}")
        
        if not self.validate_duration(duration):
            errors.append(f"Invalid duration: {duration}")
        
        if not self.validate_proximity(proximity):
            errors.append(f"Invalid proximity: {proximity}")
        
        if not self.validate_calendar(calendar):
            errors.append(f"Invalid calendar: {calendar}")
        
        if not self.validate_direction(direction):
            errors.append(f"Invalid direction: {direction}")
        
        if not self.validate_generation(generation):
            errors.append(f"Invalid generation: {generation}")
        
        return len(errors) == 0, errors
    
    def get_vocabulary_summary(self) -> str:
        """Generate a human-readable vocabulary summary."""
        lines = []
        lines.append("# Re-entry Vocabulary Summary")
        lines.append("")
        
        lines.append("## Duration Buckets")
        for bucket in self.vocab_data.get("duration_buckets", []):
            max_min = bucket["max_minutes"] or "unlimited"
            lines.append(f"- **{bucket['token']}**: {bucket['desc']} (max: {max_min} minutes)")
        lines.append("")
        
        lines.append("## Proximity Buckets")
        for bucket in self.vocab_data.get("proximity_buckets", []):
            window = bucket["window_minutes"]
            lines.append(f"- **{bucket['token']}**: {bucket['desc']} ({window[0]} to {window[1]} minutes)")
        lines.append("")
        
        lines.append("## Outcome Buckets")
        for bucket in self.vocab_data.get("outcome_buckets", []):
            lines.append(f"- **{bucket['token']}** (rank {bucket['rank']}): {bucket['desc']}")
        lines.append("")
        
        lines.append("## Direction Options")
        for direction in self.get_direction_tokens():
            lines.append(f"- **{direction}**")
        lines.append("")
        
        min_gen, max_gen = self.get_generation_range()
        lines.append(f"## Generation Range: {min_gen} to {max_gen}")
        lines.append("- 1: Original trade (O)")
        lines.append("- 2: First re-entry (R1)")  
        lines.append("- 3: Second re-entry (R2)")
        
        return "\n".join(lines)