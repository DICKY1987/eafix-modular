# DOC_ID: DOC-SERVICE-0082
"""
Re-entry Decision Processor

Processes re-entry requests using the shared library for hybrid ID management
and the tiered resolver for parameter determination. Implements CSV atomic writes
for ReentryDecision records.
"""

import sys
import os
import asyncio
import csv
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

import structlog

# Add shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from shared.reentry import HybridIdHelper, ReentryVocabulary, compose, parse, validate_key
from contracts.models import ReentryDecision

logger = structlog.get_logger(__name__)


class ReentryProcessor:
    """Processes re-entry decisions with shared library integration."""
    
    def __init__(self, settings, metrics):
        self.settings = settings
        self.metrics = metrics
        
        # Initialize shared library components
        try:
            vocab_path = self.settings.get_vocabulary_file_path()
            self.vocabulary = ReentryVocabulary(vocab_path if vocab_path.exists() else None)
            self.hybrid_helper = HybridIdHelper(self.vocabulary)
            logger.info("Initialized shared library components", vocab_file=str(vocab_path))
        except Exception as e:
            logger.error("Failed to initialize shared library", error=str(e))
            raise
        
        self.csv_sequence = 1
        self._sequence_lock = asyncio.Lock()
    
    async def process_reentry_decision(self, request) -> Dict[str, Any]:
        """Process a re-entry decision request."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info(
                "Processing re-entry decision",
                trade_id=request.trade_id,
                symbol=request.symbol,
                outcome=request.outcome_class,
                generation=request.generation
            )
            
            # Import resolver here to avoid circular import
            from .resolver import TieredParameterResolver
            resolver = TieredParameterResolver(self.settings)
            await resolver.load_parameter_sets()
            
            # Resolve parameters using tiered logic
            resolved_params = await resolver.resolve_parameters(
                request.outcome_class,
                request.duration_class, 
                request.proximity_state,
                request.calendar_id,
                request.symbol,
                request.generation
            )
            
            # Generate hybrid ID using shared library
            hybrid_id = self._compose_hybrid_id(request, resolved_params)
            
            # Determine re-entry action
            reentry_action = self._determine_reentry_action(request, resolved_params)
            
            # Calculate position sizing and levels
            lot_size = self._calculate_lot_size(request, resolved_params)
            stop_loss = resolved_params["stop_loss_pips"]
            take_profit = resolved_params["take_profit_pips"]
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(request, resolved_params)
            
            # Get chain position
            chain_position = self.hybrid_helper.get_chain_position(request.generation)
            
            # Create decision record
            decision = {
                "trade_id": request.trade_id,
                "hybrid_id": hybrid_id,
                "symbol": request.symbol,
                "outcome_class": request.outcome_class,
                "duration_class": request.duration_class,
                "reentry_action": reentry_action,
                "parameter_set_id": resolved_params["parameter_set_id"],
                "resolved_tier": resolved_params["resolved_tier"],
                "chain_position": chain_position,
                "lot_size": lot_size,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence_score": confidence_score,
                "processing_time_ms": (asyncio.get_event_loop().time() - start_time) * 1000
            }
            
            # Write to CSV using atomic policy
            await self._write_reentry_decision_csv(decision)
            
            # Record metrics
            processing_time = asyncio.get_event_loop().time() - start_time
            self.metrics.record_decision_processed(processing_time)
            
            logger.info(
                "Re-entry decision completed",
                trade_id=request.trade_id,
                hybrid_id=hybrid_id,
                reentry_action=reentry_action,
                resolved_tier=resolved_params["resolved_tier"],
                confidence_score=confidence_score
            )
            
            return decision
            
        except Exception as e:
            logger.error(
                "Failed to process re-entry decision",
                trade_id=request.trade_id,
                error=str(e),
                exc_info=True
            )
            self.metrics.record_error("processing_error")
            raise
    
    def _compose_hybrid_id(self, request, resolved_params: Dict[str, Any]) -> str:
        """Compose hybrid ID using shared library."""
        try:
            # Map request values to vocabulary tokens
            outcome_token = self._map_outcome_to_token(request.outcome_class)
            
            # Use shared library to compose ID
            hybrid_id = compose(
                outcome=outcome_token,
                duration=request.duration_class,
                proximity=request.proximity_state,
                calendar=request.calendar_id,
                direction=request.direction,
                generation=request.generation
            )
            
            # Validate the composed ID
            if not validate_key(hybrid_id):
                logger.warning("Composed hybrid ID failed validation", hybrid_id=hybrid_id)
                
            return hybrid_id
            
        except Exception as e:
            logger.error("Failed to compose hybrid ID", error=str(e))
            # Fallback to manual composition
            return f"{request.outcome_class}_{request.duration_class}_{request.proximity_state}_{request.calendar_id}_{request.direction}_{request.generation}"
    
    def _map_outcome_to_token(self, outcome_class: str) -> str:
        """Map outcome class to vocabulary token."""
        mapping = {
            "WIN": "W1",  # Default to W1, could be refined based on profit amount
            "LOSS": "L1", # Default to L1, could be refined based on loss amount
            "BREAKEVEN": "BE"
        }
        return mapping.get(outcome_class, "BE")
    
    def _determine_reentry_action(self, request, resolved_params: Dict[str, Any]) -> str:
        """Determine the re-entry action based on parameters."""
        if not resolved_params["reentry_enabled"]:
            return "NO_REENTRY"
        
        if not resolved_params["generation_allowed"]:
            return "NO_REENTRY"
        
        # Check generation limits
        if request.generation >= resolved_params["max_generation"]:
            return "HOLD"
        
        # Determine next action based on current generation
        next_gen = request.generation + 1
        if next_gen == 2:
            return "R1"
        elif next_gen == 3:
            return "R2"
        else:
            return "HOLD"
    
    def _calculate_lot_size(self, request, resolved_params: Dict[str, Any]) -> float:
        """Calculate lot size for re-entry."""
        base_lot_size = request.current_lot_size
        multiplier = resolved_params["lot_size_multiplier"]
        
        # Apply multiplier
        new_lot_size = base_lot_size * multiplier
        
        # Round to standard lot increments
        return round(new_lot_size, 2)
    
    def _calculate_confidence_score(self, request, resolved_params: Dict[str, Any]) -> float:
        """Calculate confidence score for the re-entry decision."""
        base_confidence = resolved_params["confidence_threshold"]
        
        # Adjust based on specificity of parameter match
        specificity_score = resolved_params.get("specificity_score", 0.0)
        
        # Adjust based on outcome class
        outcome_adjustment = 0.0
        if request.outcome_class == "WIN":
            outcome_adjustment = 0.1  # Slight boost for winning trades
        elif request.outcome_class == "LOSS":
            outcome_adjustment = -0.1  # Slight penalty for losing trades
        
        # Adjust based on generation (later generations are less confident)
        generation_adjustment = -0.05 * (request.generation - 1)
        
        # Calculate final confidence
        confidence = base_confidence + (specificity_score * 0.2) + outcome_adjustment + generation_adjustment
        
        # Clamp to valid range
        return max(0.0, min(1.0, confidence))
    
    async def _write_reentry_decision_csv(self, decision: Dict[str, Any]) -> None:
        """Write re-entry decision to CSV using atomic write policy."""
        if not self.settings.csv_atomic_writes:
            return
        
        try:
            output_dir = self.settings.get_output_path()
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"reentry_decisions_{timestamp_str}.csv"
            csv_filepath = output_dir / csv_filename
            
            # Get next sequence number
            async with self._sequence_lock:
                file_seq = self.csv_sequence
                self.csv_sequence += 1
            
            # Create ReentryDecision model for validation
            csv_record = ReentryDecision(
                file_seq=file_seq,
                timestamp=datetime.utcnow(),
                checksum_sha256="placeholder",  # Will be computed
                
                trade_id=decision["trade_id"],
                hybrid_id=decision["hybrid_id"],
                symbol=decision["symbol"],
                outcome_class=decision["outcome_class"].upper(),
                duration_class=decision["duration_class"].upper(),
                reentry_action=decision["reentry_action"],
                parameter_set_id=decision["parameter_set_id"],
                resolved_tier=decision["resolved_tier"],
                chain_position=decision["chain_position"],
                lot_size=decision["lot_size"],
                stop_loss=decision["stop_loss"],
                take_profit=decision["take_profit"]
            )
            
            # Compute checksum
            csv_record.checksum_sha256 = csv_record.compute_checksum()
            
            # Verify checksum 
            if not csv_record.verify_checksum():
                raise ValueError("Checksum verification failed")
            
            # Atomic write process
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.tmp',
                dir=output_dir,
                delete=False,
                newline=''
            ) as tmp_file:
                
                writer = csv.writer(tmp_file)
                
                # Write header if new file
                if not csv_filepath.exists():
                    header = [
                        "file_seq", "checksum_sha256", "timestamp",
                        "trade_id", "hybrid_id", "symbol", "outcome_class", "duration_class",
                        "reentry_action", "parameter_set_id", "resolved_tier", "chain_position",
                        "lot_size", "stop_loss", "take_profit"
                    ]
                    writer.writerow(header)
                
                # Write data row
                row = [
                    csv_record.file_seq,
                    csv_record.checksum_sha256,
                    csv_record.timestamp.isoformat(),
                    csv_record.trade_id,
                    csv_record.hybrid_id,
                    csv_record.symbol,
                    csv_record.outcome_class,
                    csv_record.duration_class,
                    csv_record.reentry_action,
                    csv_record.parameter_set_id,
                    csv_record.resolved_tier,
                    csv_record.chain_position,
                    csv_record.lot_size,
                    csv_record.stop_loss,
                    csv_record.take_profit
                ]
                
                writer.writerow(row)
                
                # Ensure data is written to disk
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                
                tmp_filepath = Path(tmp_file.name)
            
            # Atomic rename to final filename
            if csv_filepath.exists():
                # Append to existing file
                with open(csv_filepath, 'a', newline='') as f:
                    with open(tmp_filepath, 'r') as tmp_f:
                        # Skip header line from temp file if file already exists
                        lines = tmp_f.readlines()
                        if len(lines) > 1:  # Has header + data
                            f.write(lines[-1])  # Write only the data line
                        elif len(lines) == 1:  # Only data line
                            f.write(lines[0])
                
                # Remove temp file
                tmp_filepath.unlink()
            else:
                # Rename temp file to final name
                tmp_filepath.rename(csv_filepath)
            
            logger.info(
                "Wrote re-entry decision to CSV",
                file=str(csv_filepath),
                file_seq=file_seq,
                checksum=csv_record.checksum_sha256[:8]
            )
            
            # Record metrics
            self.metrics.increment_counter("csv_writes_total")
            
        except Exception as e:
            logger.error("Failed to write CSV", error=str(e))
            self.metrics.record_error("csv_write_error")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """Get processor status information."""
        return {
            "csv_sequence": self.csv_sequence,
            "shared_library_loaded": self.hybrid_helper is not None,
            "vocabulary_loaded": self.vocabulary is not None,
            "atomic_writes_enabled": self.settings.csv_atomic_writes,
            "output_directory": str(self.settings.get_output_path())
        }