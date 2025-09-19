"""
Tiered Parameter Resolver

Implements the tiered parameter resolution system for re-entry decisions.
Provides fallback hierarchy: EXACT → TIER1 → TIER2 → TIER3 → GLOBAL
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ParameterSet(BaseModel):
    """Re-entry parameter set definition."""
    
    id: str = Field(..., description="Unique parameter set identifier")
    name: str = Field(..., description="Human-readable name")
    tier: str = Field(..., description="Parameter tier (EXACT, TIER1, etc.)")
    
    # Matching criteria
    outcome_class: Optional[str] = Field(None, description="Specific outcome class")
    duration_class: Optional[str] = Field(None, description="Specific duration class")
    proximity_state: Optional[str] = Field(None, description="Specific proximity state")
    calendar_pattern: Optional[str] = Field(None, description="Calendar ID pattern")
    symbol_pattern: Optional[str] = Field(None, description="Symbol pattern")
    
    # Re-entry parameters
    reentry_enabled: bool = Field(True, description="Whether re-entry is enabled")
    max_generation: int = Field(3, description="Maximum re-entry generation")
    lot_size_multiplier: float = Field(1.0, description="Lot size multiplier")
    stop_loss_pips: float = Field(20.0, description="Stop loss in pips")
    take_profit_pips: float = Field(40.0, description="Take profit in pips")
    confidence_threshold: float = Field(0.6, description="Minimum confidence")
    
    # Timing parameters  
    min_wait_minutes: int = Field(0, description="Minimum wait before re-entry")
    max_wait_minutes: int = Field(60, description="Maximum wait before re-entry")
    
    # Market condition filters
    volatility_threshold: Optional[float] = Field(None, description="Required volatility level")
    spread_threshold: Optional[float] = Field(None, description="Maximum allowed spread")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = Field(True, description="Whether parameter set is active")
    
    def matches_criteria(self, outcome: str, duration: str, proximity: str, 
                        calendar: str, symbol: str) -> Tuple[bool, float]:
        """
        Check if this parameter set matches the given criteria.
        
        Returns:
            (matches, specificity_score): Boolean match and specificity score (0.0-1.0)
        """
        if not self.active:
            return False, 0.0
        
        score = 0.0
        max_score = 0.0
        
        # Check outcome class
        if self.outcome_class is not None:
            max_score += 1.0
            if outcome == self.outcome_class:
                score += 1.0
            else:
                return False, 0.0
        
        # Check duration class
        if self.duration_class is not None:
            max_score += 1.0
            if duration == self.duration_class:
                score += 1.0
            else:
                return False, 0.0
        
        # Check proximity state
        if self.proximity_state is not None:
            max_score += 1.0
            if proximity == self.proximity_state:
                score += 1.0
            else:
                return False, 0.0
        
        # Check calendar pattern
        if self.calendar_pattern is not None:
            max_score += 1.0
            if self._matches_pattern(calendar, self.calendar_pattern):
                score += 1.0
            else:
                return False, 0.0
        
        # Check symbol pattern
        if self.symbol_pattern is not None:
            max_score += 1.0
            if self._matches_pattern(symbol, self.symbol_pattern):
                score += 1.0
            else:
                return False, 0.0
        
        # Calculate specificity score
        if max_score == 0.0:
            return True, 0.0  # Global/wildcard match
        
        specificity = score / max_score
        return True, specificity
    
    def _matches_pattern(self, value: str, pattern: str) -> bool:
        """Check if value matches pattern (supports wildcards)."""
        if pattern == "*":
            return True
        elif pattern.endswith("*"):
            prefix = pattern[:-1]
            return value.startswith(prefix)
        elif pattern.startswith("*"):
            suffix = pattern[1:]
            return value.endswith(suffix)
        else:
            return value == pattern


class TieredParameterResolver:
    """Resolves parameters using tiered fallback logic."""
    
    def __init__(self, settings):
        self.settings = settings
        self.parameter_sets: List[ParameterSet] = []
        self.tier_hierarchy = settings.tier_hierarchy
        self.loaded_at: Optional[datetime] = None
        
    async def load_parameter_sets(self) -> None:
        """Load parameter sets from configuration file."""
        try:
            param_file = self.settings.get_parameter_sets_path()
            
            if param_file.exists():
                with open(param_file, 'r') as f:
                    data = json.load(f)
                
                self.parameter_sets = [
                    ParameterSet(**param_data) 
                    for param_data in data.get("parameter_sets", [])
                ]
            else:
                # Create default parameter sets
                await self._create_default_parameter_sets()
                
            self.loaded_at = datetime.utcnow()
            
            logger.info(
                "Loaded parameter sets",
                count=len(self.parameter_sets),
                file=str(param_file)
            )
            
        except Exception as e:
            logger.error("Failed to load parameter sets", error=str(e))
            # Fall back to minimal defaults
            await self._create_minimal_defaults()
    
    async def _create_default_parameter_sets(self) -> None:
        """Create default parameter sets for all tiers."""
        defaults = [
            # GLOBAL fallback
            {
                "id": "global_default",
                "name": "Global Default Parameters",
                "tier": "GLOBAL",
                "reentry_enabled": True,
                "max_generation": 3,
                "lot_size_multiplier": 1.0,
                "stop_loss_pips": 20.0,
                "take_profit_pips": 40.0,
                "confidence_threshold": 0.6
            },
            
            # High-impact calendar events
            {
                "id": "cal8_high_impact",
                "name": "CAL8 High Impact Events",
                "tier": "TIER1",
                "calendar_pattern": "CAL8_*",
                "reentry_enabled": True,
                "lot_size_multiplier": 0.8,
                "stop_loss_pips": 15.0,
                "take_profit_pips": 30.0,
                "confidence_threshold": 0.7
            },
            
            # Win outcomes - more aggressive re-entry
            {
                "id": "win_outcomes",
                "name": "Win Outcome Re-entries",
                "tier": "TIER2", 
                "outcome_class": "WIN",
                "lot_size_multiplier": 1.2,
                "stop_loss_pips": 25.0,
                "take_profit_pips": 50.0,
                "confidence_threshold": 0.5
            },
            
            # Loss outcomes - conservative re-entry
            {
                "id": "loss_outcomes",
                "name": "Loss Outcome Re-entries",
                "tier": "TIER2",
                "outcome_class": "LOSS",
                "lot_size_multiplier": 0.7,
                "stop_loss_pips": 15.0,
                "take_profit_pips": 30.0,
                "confidence_threshold": 0.8
            },
            
            # Flash duration - no re-entry
            {
                "id": "flash_no_reentry",
                "name": "Flash Duration - No Re-entry",
                "tier": "TIER3",
                "duration_class": "FLASH",
                "reentry_enabled": False,
                "confidence_threshold": 1.0  # Effectively disabled
            }
        ]
        
        self.parameter_sets = [ParameterSet(**param) for param in defaults]
        
        # Save defaults to file
        await self._save_parameter_sets()
    
    async def _create_minimal_defaults(self) -> None:
        """Create minimal fallback parameter set."""
        self.parameter_sets = [
            ParameterSet(
                id="emergency_default",
                name="Emergency Default",
                tier="GLOBAL",
                reentry_enabled=True,
                max_generation=2,
                lot_size_multiplier=1.0,
                stop_loss_pips=30.0,
                take_profit_pips=60.0,
                confidence_threshold=0.7
            )
        ]
    
    async def _save_parameter_sets(self) -> None:
        """Save parameter sets to configuration file."""
        try:
            param_file = self.settings.get_parameter_sets_path()
            param_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "parameter_sets": [param.dict() for param in self.parameter_sets],
                "last_updated": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
            
            with open(param_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
            logger.info("Saved parameter sets", file=str(param_file))
            
        except Exception as e:
            logger.error("Failed to save parameter sets", error=str(e))
    
    async def resolve_parameters(self, outcome: str, duration: str, proximity: str,
                               calendar: str, symbol: str, generation: int) -> Dict[str, Any]:
        """
        Resolve parameters using tiered fallback logic.
        
        Returns resolved parameter set with metadata about which tier was used.
        """
        logger.info(
            "Resolving parameters",
            outcome=outcome,
            duration=duration,
            proximity=proximity,
            calendar=calendar,
            symbol=symbol,
            generation=generation
        )
        
        best_match = None
        best_score = -1.0
        resolved_tier = "NONE"
        
        # Try each tier in hierarchy order
        for tier in self.tier_hierarchy:
            candidates = [p for p in self.parameter_sets if p.tier == tier]
            
            for param_set in candidates:
                matches, score = param_set.matches_criteria(
                    outcome, duration, proximity, calendar, symbol
                )
                
                if matches and score > best_score:
                    best_match = param_set
                    best_score = score
                    resolved_tier = tier
                    
                    # If exact match, stop searching
                    if tier == "EXACT" and score == 1.0:
                        break
            
            # If we found a match in this tier, stop (hierarchical fallback)
            if best_match:
                break
        
        if not best_match:
            logger.error("No parameter set found - using emergency defaults")
            # Create emergency default
            best_match = ParameterSet(
                id="emergency_fallback",
                name="Emergency Fallback",
                tier="EMERGENCY",
                reentry_enabled=False,
                confidence_threshold=1.0
            )
            resolved_tier = "EMERGENCY"
        
        # Build response
        result = {
            "parameter_set_id": best_match.id,
            "parameter_set_name": best_match.name,
            "resolved_tier": resolved_tier,
            "specificity_score": best_score,
            
            # Core parameters
            "reentry_enabled": best_match.reentry_enabled,
            "max_generation": best_match.max_generation,
            "lot_size_multiplier": best_match.lot_size_multiplier,
            "stop_loss_pips": best_match.stop_loss_pips,
            "take_profit_pips": best_match.take_profit_pips,
            "confidence_threshold": best_match.confidence_threshold,
            
            # Timing
            "min_wait_minutes": best_match.min_wait_minutes,
            "max_wait_minutes": best_match.max_wait_minutes,
            
            # Conditions
            "volatility_threshold": best_match.volatility_threshold,
            "spread_threshold": best_match.spread_threshold,
            
            # Generation check
            "generation_allowed": generation <= best_match.max_generation,
            "next_generation": generation + 1 if generation < best_match.max_generation else None
        }
        
        logger.info(
            "Resolved parameters",
            parameter_set_id=result["parameter_set_id"],
            resolved_tier=resolved_tier,
            specificity_score=best_score,
            reentry_enabled=result["reentry_enabled"]
        )
        
        return result
    
    async def get_parameter_sets_for_tier(self, tier: str) -> List[Dict[str, Any]]:
        """Get all parameter sets for a specific tier."""
        return [
            param.dict() for param in self.parameter_sets 
            if param.tier == tier and param.active
        ]
    
    async def get_status(self) -> Dict[str, Any]:
        """Get resolver status information."""
        active_sets = sum(1 for p in self.parameter_sets if p.active)
        
        tier_counts = {}
        for tier in self.tier_hierarchy:
            tier_counts[tier] = sum(
                1 for p in self.parameter_sets 
                if p.tier == tier and p.active
            )
        
        return {
            "total_parameter_sets": len(self.parameter_sets),
            "active_parameter_sets": active_sets,
            "tier_hierarchy": self.tier_hierarchy,
            "tier_counts": tier_counts,
            "loaded_at": self.loaded_at.isoformat() if self.loaded_at else None,
            "fallback_enabled": self.settings.tier_fallback_enabled
        }