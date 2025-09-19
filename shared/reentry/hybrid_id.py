"""
Hybrid ID Composition and Parsing

Provides deterministic functions for composing, parsing, and validating hybrid IDs.
Maintains cross-language parity with MQL4 implementation.
"""

import hashlib
import logging
import re
from typing import Dict, Optional, Tuple, List

from .vocab import ReentryVocabulary

logger = logging.getLogger(__name__)


class HybridIdHelper:
    """Helper class for hybrid ID operations with vocabulary validation."""
    
    def __init__(self, vocabulary: Optional[ReentryVocabulary] = None):
        """Initialize with vocabulary instance."""
        self.vocab = vocabulary or ReentryVocabulary()
    
    def compose(self, outcome: str, duration: str, proximity: str, calendar: str, 
                direction: str, generation: int, suffix: Optional[str] = None) -> str:
        """
        Compose a hybrid ID from components.
        
        Args:
            outcome: Trade outcome (W2, W1, BE, L1, L2)
            duration: Duration class (FLASH, QUICK, LONG, EXTENDED)
            proximity: Proximity to event (PRE_1H, AT_EVENT, POST_30M)
            calendar: Calendar identifier (CAL8_*, CAL5_*, NONE)
            direction: Trade direction (LONG, SHORT, ANY)
            generation: Generation number (1-3)
            suffix: Optional comment suffix hash
            
        Returns:
            Composed hybrid ID string
            
        Raises:
            ValueError: If any component is invalid
        """
        # Validate all components
        valid, errors = self.vocab.is_valid_hybrid_context(
            outcome, duration, proximity, calendar, direction, generation
        )
        
        if not valid:
            raise ValueError(f"Invalid hybrid ID components: {'; '.join(errors)}")
        
        # Compose base ID
        components = [outcome, duration, proximity, calendar, direction, str(generation)]
        base_id = '_'.join(components)
        
        # Add suffix if provided
        if suffix:
            if not re.match(r'^[a-z0-9]{6}$', suffix):
                raise ValueError(f"Invalid suffix format: {suffix} (must be 6 alphanumeric lowercase)")
            return f"{base_id}_{suffix}"
        
        return base_id
    
    def parse(self, hybrid_id: str) -> Dict[str, str]:
        """
        Parse a hybrid ID into components.
        
        Args:
            hybrid_id: Hybrid ID string to parse
            
        Returns:
            Dictionary with parsed components
            
        Raises:
            ValueError: If hybrid ID format is invalid
        """
        if not isinstance(hybrid_id, str) or not hybrid_id:
            raise ValueError("Hybrid ID must be a non-empty string")
        
        parts = hybrid_id.split('_')
        
        if len(parts) < 6:
            raise ValueError(f"Hybrid ID must have at least 6 components, got {len(parts)}: {hybrid_id}")
        
        # Basic extraction
        outcome = parts[0]
        duration = parts[1] 
        proximity = parts[2]
        
        # Handle calendar IDs that may contain underscores
        # Find where generation starts (should be a number)
        generation_idx = None
        for i in range(3, len(parts)):
            if parts[i].isdigit():
                generation_idx = i
                break
        
        if generation_idx is None:
            raise ValueError(f"No valid generation found in hybrid ID: {hybrid_id}")
        
        # Reconstruct calendar from parts between proximity and generation
        calendar_parts = parts[3:generation_idx]
        calendar = '_'.join(calendar_parts) if calendar_parts else "NONE"
        
        # Extract generation and direction
        if generation_idx == len(parts) - 1:
            # No direction specified, generation is last
            raise ValueError(f"Missing direction component in hybrid ID: {hybrid_id}")
        
        # Direction should be the part before generation
        direction = parts[generation_idx - 1] if generation_idx > 3 else parts[generation_idx + 1]
        generation_str = parts[generation_idx]
        
        # Check for suffix (after generation)
        suffix = None
        if len(parts) > generation_idx + 1:
            potential_suffix = parts[-1]
            if re.match(r'^[a-z0-9]{6}$', potential_suffix):
                suffix = potential_suffix
        
        # Validate parsed components
        try:
            generation = int(generation_str)
        except ValueError:
            raise ValueError(f"Invalid generation: {generation_str}")
        
        # Re-parse more carefully for standard format
        # Expected: outcome_duration_proximity_calendar_direction_generation[_suffix]
        if len(parts) >= 6:
            outcome = parts[0]
            duration = parts[1]
            proximity = parts[2]
            
            # Find direction and generation by working backwards
            # Generation is always numeric and near the end
            generation_found = False
            
            # Look for generation (numeric) from the end
            for i in range(len(parts) - 1, 2, -1):  # Start from end, go backwards
                if parts[i].isdigit():
                    try:
                        generation = int(parts[i])
                        generation_idx = i
                        generation_found = True
                        break
                    except ValueError:
                        continue
            
            if not generation_found:
                raise ValueError(f"No valid generation found in hybrid ID: {hybrid_id}")
            
            # Direction should be just before generation
            if generation_idx > 3:
                direction = parts[generation_idx - 1]
                
                # Calendar is everything between proximity and direction
                calendar_parts = parts[3:generation_idx - 1]
                calendar = '_'.join(calendar_parts) if calendar_parts else "NONE"
                
                # Suffix is optional after generation
                if generation_idx + 1 < len(parts):
                    potential_suffix = parts[generation_idx + 1]
                    if re.match(r'^[a-z0-9]{6}$', potential_suffix):
                        suffix = potential_suffix
            else:
                raise ValueError(f"Invalid hybrid ID structure: {hybrid_id}")
        
        # Validate parsed components
        valid, errors = self.vocab.is_valid_hybrid_context(
            outcome, duration, proximity, calendar, direction, generation
        )
        
        if not valid:
            logger.warning(f"Parsed components may be invalid: {'; '.join(errors)}")
        
        result = {
            "outcome": outcome,
            "duration": duration,
            "proximity": proximity,
            "calendar": calendar,
            "direction": direction,
            "generation": str(generation),
        }
        
        if suffix:
            result["suffix"] = suffix
        
        return result
    
    def validate_key(self, hybrid_id: str) -> bool:
        """
        Validate hybrid ID format and vocabulary compliance.
        
        Args:
            hybrid_id: Hybrid ID string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            components = self.parse(hybrid_id)
            
            # Validate each component
            return self.vocab.is_valid_hybrid_context(
                components["outcome"],
                components["duration"], 
                components["proximity"],
                components["calendar"],
                components["direction"],
                int(components["generation"])
            )[0]
            
        except Exception as e:
            logger.debug(f"Validation failed for {hybrid_id}: {e}")
            return False
    
    def comment_suffix_hash(self, hybrid_id: str) -> str:
        """
        Generate deterministic 6-character suffix for trade comments.
        
        Must produce identical results to MQL4 implementation for cross-language parity.
        
        Args:
            hybrid_id: Hybrid ID to generate suffix for
            
        Returns:
            6-character lowercase alphanumeric suffix
        """
        # Use SHA-256 for deterministic hashing
        hash_input = hybrid_id.encode('utf-8')
        sha256_hash = hashlib.sha256(hash_input).hexdigest()
        
        # Take first 6 characters and ensure they're valid
        # Use only alphanumeric characters, avoid confusing ones
        valid_chars = '0123456789abcdefghijklmnopqrstuvwxyz'
        
        suffix_chars = []
        hash_idx = 0
        
        while len(suffix_chars) < 6 and hash_idx < len(sha256_hash):
            char = sha256_hash[hash_idx]
            if char in valid_chars:
                suffix_chars.append(char)
            hash_idx += 1
        
        # If we don't have enough valid characters, pad with hash of the hash
        while len(suffix_chars) < 6:
            sha256_hash = hashlib.sha256(sha256_hash.encode()).hexdigest()
            for char in sha256_hash:
                if char in valid_chars and len(suffix_chars) < 6:
                    suffix_chars.append(char)
                if len(suffix_chars) >= 6:
                    break
        
        return ''.join(suffix_chars[:6])
    
    def validate_comment_suffix_parity(self, hybrid_id: str, expected_suffix: str) -> bool:
        """
        Validate that our suffix generation matches expected result (e.g., from MQL4).
        
        Args:
            hybrid_id: Hybrid ID string
            expected_suffix: Expected suffix from other implementation
            
        Returns:
            True if suffixes match, False otherwise
        """
        generated_suffix = self.comment_suffix_hash(hybrid_id)
        return generated_suffix == expected_suffix
    
    def get_chain_position(self, generation: int) -> str:
        """
        Get chain position label from generation number.
        
        Args:
            generation: Generation number (1-3)
            
        Returns:
            Chain position (O, R1, R2)
        """
        if generation == 1:
            return "O"
        elif generation == 2:
            return "R1" 
        elif generation == 3:
            return "R2"
        else:
            raise ValueError(f"Invalid generation for chain position: {generation}")
    
    def get_next_generation(self, current_generation: int) -> Optional[int]:
        """
        Get next valid generation number for re-entries.
        
        Args:
            current_generation: Current generation number
            
        Returns:
            Next generation number or None if at maximum
        """
        min_gen, max_gen = self.vocab.get_generation_range()
        
        if current_generation >= max_gen:
            return None
        
        return current_generation + 1
    
    def decompose_for_comment(self, hybrid_id: str) -> str:
        """
        Create abbreviated form suitable for MT4 comments (31 char limit).
        
        Args:
            hybrid_id: Full hybrid ID
            
        Returns:
            Abbreviated comment string
        """
        try:
            components = self.parse(hybrid_id)
            suffix = self.comment_suffix_hash(hybrid_id)
            
            # Create abbreviated form: outcome_dur_prox_gen_suffix
            short_form = f"{components['outcome']}_{components['duration'][:4]}_{components['proximity'][:2]}_{components['generation']}_{suffix}"
            
            # Ensure it fits in 31 characters
            if len(short_form) > 31:
                # Ultra-short form: outcome_gen_suffix 
                short_form = f"{components['outcome']}_{components['generation']}_{suffix}"
            
            return short_form
            
        except Exception as e:
            logger.error(f"Failed to decompose for comment: {e}")
            # Fallback to just suffix
            return self.comment_suffix_hash(hybrid_id)


# Global instance for convenience functions
_global_helper = HybridIdHelper()


def compose(outcome: str, duration: str, proximity: str, calendar: str, 
           direction: str, generation: int, suffix: Optional[str] = None) -> str:
    """Global convenience function for composing hybrid IDs."""
    return _global_helper.compose(outcome, duration, proximity, calendar, direction, generation, suffix)


def parse(hybrid_id: str) -> Dict[str, str]:
    """Global convenience function for parsing hybrid IDs."""
    return _global_helper.parse(hybrid_id)


def validate_key(hybrid_id: str) -> bool:
    """Global convenience function for validating hybrid IDs."""
    return _global_helper.validate_key(hybrid_id)


def comment_suffix_hash(hybrid_id: str) -> str:
    """Global convenience function for generating comment suffixes."""
    return _global_helper.comment_suffix_hash(hybrid_id)