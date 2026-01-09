# DOC_ID: DOC-SERVICE-0076
"""
Trade Result Processor

Processes completed trades, classifies outcomes and durations,
integrates with re-entry matrix service for decisions, and implements
atomic CSV writes for ReentryDecision records.
"""

import sys
import asyncio
import csv
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

import structlog

# Add shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from shared.reentry import HybridIdHelper, ReentryVocabulary, compose, parse, validate_key
from contracts.models import TradeResult, ReentryDecision

logger = structlog.get_logger(__name__)


class TradeResultProcessor:
    """Processes trade results for re-entry analysis."""
    
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
        
        # Processing state
        self.csv_sequence = 1
        self._sequence_lock = asyncio.Lock()
        self.recent_decisions: List[Dict[str, Any]] = []
        self._decisions_lock = asyncio.Lock()
        
        # Cooldown tracking
        self.symbol_cooldowns: Dict[str, datetime] = {}
        self.daily_attempt_counts: Dict[str, int] = {}
        self.last_reset_date = datetime.utcnow().date()
        
        self.running = False
    
    async def start(self) -> None:
        """Start the processor."""
        self.running = True
        logger.info("Trade result processor started")
    
    async def stop(self) -> None:
        """Stop the processor."""
        self.running = False
        logger.info("Trade result processor stopped")
    
    async def process_trade_result(self, trade_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single trade result for re-entry analysis.
        
        Returns processing result with decision information.
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info(
                "Processing trade result",
                trade_id=trade_result.get("trade_id"),
                symbol=trade_result.get("symbol"),
                profit_loss=trade_result.get("profit_loss_pips")
            )
            
            # Validate trade result structure
            validated_trade = await self._validate_trade_result(trade_result)
            
            # Check eligibility for re-entry processing
            eligibility = await self._check_reentry_eligibility(validated_trade)
            if not eligibility["eligible"]:
                logger.info(
                    "Trade not eligible for re-entry",
                    trade_id=validated_trade.trade_id,
                    reason=eligibility["reason"]
                )
                return {
                    "status": "skipped",
                    "reason": eligibility["reason"],
                    "trade_id": validated_trade.trade_id
                }
            
            # Classify trade outcome and duration
            outcome_class = self._classify_trade_outcome(validated_trade)
            duration_class = self._classify_trade_duration(validated_trade)
            
            # Extract hybrid ID from trade comment if present
            existing_hybrid_id = self._extract_hybrid_id_from_comment(validated_trade.comment)
            
            # Determine proximity state (simplified - would integrate with calendar service)
            proximity_state = await self._determine_proximity_state(validated_trade)
            
            # Get calendar ID (simplified - would integrate with calendar service)
            calendar_id = await self._get_associated_calendar_id(validated_trade)
            
            # Map trade direction to re-entry direction
            direction = "LONG" if validated_trade.direction == "BUY" else "SHORT"
            
            # Determine generation (from existing hybrid ID or start at 1)
            generation = self._determine_generation(existing_hybrid_id)
            
            # Call re-entry matrix service for decision
            from .decision_client import ReentryMatrixClient
            matrix_client = ReentryMatrixClient(self.settings)
            
            decision_request = {
                "trade_id": validated_trade.trade_id,
                "symbol": validated_trade.symbol,
                "outcome_class": outcome_class,
                "duration_class": duration_class,
                "proximity_state": proximity_state,
                "calendar_id": calendar_id,
                "direction": direction,
                "generation": generation,
                "current_lot_size": validated_trade.lot_size,
                "profit_loss_pips": validated_trade.profit_loss_pips
            }
            
            decision_response = await matrix_client.request_reentry_decision(decision_request)
            
            # Update cooldown and attempt tracking
            await self._update_reentry_tracking(validated_trade.symbol, decision_response)
            
            # Create and write ReentryDecision CSV record
            csv_result = await self._write_reentry_decision_csv(validated_trade, decision_response)
            
            # Track recent decision
            await self._track_recent_decision(validated_trade, decision_response)
            
            # Record metrics
            processing_time = asyncio.get_event_loop().time() - start_time
            self.metrics.record_trade_processed(processing_time, outcome_class, duration_class)
            
            result = {
                "status": "processed",
                "trade_id": validated_trade.trade_id,
                "outcome_class": outcome_class,
                "duration_class": duration_class,
                "reentry_action": decision_response["reentry_action"],
                "hybrid_id": decision_response["hybrid_id"],
                "csv_written": csv_result["success"],
                "processing_time_ms": processing_time * 1000
            }
            
            logger.info(
                "Trade result processed successfully",
                trade_id=validated_trade.trade_id,
                outcome=outcome_class,
                duration=duration_class,
                reentry_action=decision_response["reentry_action"]
            )
            
            return result
            
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            logger.error(
                "Failed to process trade result",
                trade_id=trade_result.get("trade_id"),
                error=str(e),
                processing_time_ms=processing_time * 1000,
                exc_info=True
            )
            self.metrics.record_error("trade_processing_error")
            raise
    
    async def _validate_trade_result(self, trade_result: Dict[str, Any]) -> TradeResult:
        """Validate trade result against contract schema."""
        try:
            # Convert datetime strings to datetime objects if needed
            if isinstance(trade_result.get("open_time"), str):
                trade_result["open_time"] = datetime.fromisoformat(trade_result["open_time"].replace('Z', '+00:00'))
            
            if isinstance(trade_result.get("close_time"), str):
                trade_result["close_time"] = datetime.fromisoformat(trade_result["close_time"].replace('Z', '+00:00'))
            
            # Add placeholder values for CSV model requirements
            trade_result["file_seq"] = 0  # Will be set during CSV write
            trade_result["checksum_sha256"] = "placeholder"  # Will be computed
            trade_result["timestamp"] = datetime.utcnow()
            
            # Validate with Pydantic model
            validated = TradeResult(**trade_result)
            return validated
            
        except Exception as e:
            logger.error("Trade result validation failed", error=str(e))
            raise ValueError(f"Invalid trade result: {e}")
    
    async def _check_reentry_eligibility(self, trade_result: TradeResult) -> Dict[str, Any]:
        """Check if trade is eligible for re-entry processing."""
        
        # Check if trade is completed
        if self.settings.process_completed_trades_only and not trade_result.close_time:
            return {"eligible": False, "reason": "trade_not_completed"}
        
        # Check minimum duration
        if trade_result.duration_minutes < self.settings.min_trade_duration_minutes:
            return {"eligible": False, "reason": "duration_too_short"}
        
        # Check if manual close should be excluded
        if self.settings.exclude_manual_closes and trade_result.close_reason == "MANUAL":
            return {"eligible": False, "reason": "manual_close_excluded"}
        
        # Check cooldown period
        symbol = trade_result.symbol
        if symbol in self.symbol_cooldowns:
            cooldown_end = self.symbol_cooldowns[symbol] + timedelta(minutes=self.settings.reentry_cooldown_minutes)
            if datetime.utcnow() < cooldown_end:
                return {"eligible": False, "reason": "cooldown_period_active"}
        
        # Check daily attempt limit
        await self._reset_daily_counts_if_needed()
        if self.daily_attempt_counts.get(symbol, 0) >= self.settings.max_reentry_attempts_per_day:
            return {"eligible": False, "reason": "daily_limit_exceeded"}
        
        return {"eligible": True, "reason": "eligible"}
    
    def _classify_trade_outcome(self, trade_result: TradeResult) -> str:
        """Classify trade outcome as WIN, LOSS, or BREAKEVEN."""
        pips = trade_result.profit_loss_pips
        
        if pips >= self.settings.profit_threshold_pips:
            return "WIN"
        elif pips <= self.settings.loss_threshold_pips:
            return "LOSS"
        else:
            return "BREAKEVEN"
    
    def _classify_trade_duration(self, trade_result: TradeResult) -> str:
        """Classify trade duration as FLASH, QUICK, LONG, or EXTENDED."""
        minutes = trade_result.duration_minutes
        
        if minutes <= self.settings.flash_duration_max_minutes:
            return "FLASH"
        elif minutes <= self.settings.quick_duration_max_minutes:
            return "QUICK"
        elif minutes <= self.settings.long_duration_max_minutes:
            return "LONG"
        else:
            return "EXTENDED"
    
    def _extract_hybrid_id_from_comment(self, comment: str) -> Optional[str]:
        """Extract hybrid ID from trade comment if present."""
        try:
            # Look for hybrid ID pattern in comment
            # This is a simplified implementation - in practice, would use regex
            parts = comment.split('_')
            if len(parts) >= 6:
                # Try to validate as hybrid ID
                if validate_key(comment):
                    return comment
            return None
        except Exception:
            return None
    
    async def _determine_proximity_state(self, trade_result: TradeResult) -> str:
        """Determine proximity state relative to calendar events."""
        # Simplified implementation - in practice, would query calendar service
        # For now, use trade timing heuristics
        
        # Check if trade was opened/closed during typical news hours
        open_hour = trade_result.open_time.hour
        
        if 8 <= open_hour <= 10 or 13 <= open_hour <= 15:  # Common news times
            return "AT_EVENT"
        elif 7 <= open_hour <= 11 or 12 <= open_hour <= 16:  # Near news times
            return "PRE_1H"
        else:
            return "POST_30M"
    
    async def _get_associated_calendar_id(self, trade_result: TradeResult) -> str:
        """Get associated calendar ID for the trade."""
        # Simplified implementation - in practice, would query calendar service
        # For now, return NONE unless we can infer from trade characteristics
        
        symbol = trade_result.symbol
        
        # Major USD pairs might have CAL8 events
        if "USD" in symbol and abs(trade_result.profit_loss_pips) > 20:
            return "CAL8_USD_UNKNOWN_H"
        
        return "NONE"
    
    def _determine_generation(self, existing_hybrid_id: Optional[str]) -> int:
        """Determine generation number from existing hybrid ID or start at 1."""
        if not existing_hybrid_id:
            return 1
        
        try:
            components = parse(existing_hybrid_id)
            current_gen = int(components.get("generation", 1))
            return min(current_gen + 1, 3)  # Cap at generation 3
        except Exception:
            return 1
    
    async def _update_reentry_tracking(self, symbol: str, decision_response: Dict[str, Any]) -> None:
        """Update cooldown and attempt tracking."""
        now = datetime.utcnow()
        
        # Update cooldown
        self.symbol_cooldowns[symbol] = now
        
        # Update daily attempt count if re-entry was recommended
        if decision_response["reentry_action"] in ["R1", "R2"]:
            await self._reset_daily_counts_if_needed()
            self.daily_attempt_counts[symbol] = self.daily_attempt_counts.get(symbol, 0) + 1
    
    async def _reset_daily_counts_if_needed(self) -> None:
        """Reset daily attempt counts if new day."""
        current_date = datetime.utcnow().date()
        if current_date != self.last_reset_date:
            self.daily_attempt_counts.clear()
            self.last_reset_date = current_date
    
    async def _write_reentry_decision_csv(self, trade_result: TradeResult, 
                                        decision_response: Dict[str, Any]) -> Dict[str, Any]:
        """Write re-entry decision to CSV using atomic write policy."""
        if not self.settings.csv_atomic_writes:
            return {"success": False, "reason": "csv_writes_disabled"}
        
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
                
                trade_id=trade_result.trade_id,
                hybrid_id=decision_response["hybrid_id"],
                symbol=trade_result.symbol,
                outcome_class=self._classify_trade_outcome(trade_result).upper(),
                duration_class=self._classify_trade_duration(trade_result).upper(),
                reentry_action=decision_response["reentry_action"],
                parameter_set_id=decision_response["parameter_set_id"],
                resolved_tier=decision_response["resolved_tier"],
                chain_position=decision_response["chain_position"],
                lot_size=decision_response["lot_size"],
                stop_loss=decision_response["stop_loss"],
                take_profit=decision_response["take_profit"]
            )
            
            # Compute and verify checksum
            csv_record.checksum_sha256 = csv_record.compute_checksum()
            if not csv_record.verify_checksum():
                raise ValueError("Checksum verification failed")
            
            # Atomic write process (same as reentry-matrix-svc)
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
                    csv_record.file_seq, csv_record.checksum_sha256, csv_record.timestamp.isoformat(),
                    csv_record.trade_id, csv_record.hybrid_id, csv_record.symbol,
                    csv_record.outcome_class, csv_record.duration_class, csv_record.reentry_action,
                    csv_record.parameter_set_id, csv_record.resolved_tier, csv_record.chain_position,
                    csv_record.lot_size, csv_record.stop_loss, csv_record.take_profit
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
                        lines = tmp_f.readlines()
                        if len(lines) > 1:  # Has header + data
                            f.write(lines[-1])  # Write only the data line
                        elif len(lines) == 1:  # Only data line
                            f.write(lines[0])
                tmp_filepath.unlink()
            else:
                tmp_filepath.rename(csv_filepath)
            
            logger.info(
                "Wrote re-entry decision to CSV",
                file=str(csv_filepath),
                file_seq=file_seq,
                checksum=csv_record.checksum_sha256[:8]
            )
            
            self.metrics.increment_counter("csv_writes_total")
            
            return {
                "success": True,
                "file": str(csv_filepath),
                "file_seq": file_seq,
                "checksum": csv_record.checksum_sha256
            }
            
        except Exception as e:
            logger.error("Failed to write CSV", error=str(e))
            self.metrics.record_error("csv_write_error")
            return {"success": False, "error": str(e)}
    
    async def _track_recent_decision(self, trade_result: TradeResult, 
                                   decision_response: Dict[str, Any]) -> None:
        """Track recent decision for status reporting."""
        async with self._decisions_lock:
            decision_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "trade_id": trade_result.trade_id,
                "symbol": trade_result.symbol,
                "outcome_class": self._classify_trade_outcome(trade_result),
                "duration_class": self._classify_trade_duration(trade_result),
                "reentry_action": decision_response["reentry_action"],
                "hybrid_id": decision_response["hybrid_id"],
                "confidence_score": decision_response["confidence_score"]
            }
            
            self.recent_decisions.append(decision_record)
            
            # Keep only last 100 decisions
            if len(self.recent_decisions) > 100:
                self.recent_decisions = self.recent_decisions[-100:]
    
    async def get_recent_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent re-entry decisions."""
        async with self._decisions_lock:
            return self.recent_decisions[-limit:] if limit > 0 else self.recent_decisions
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "csv_sequence": self.csv_sequence,
            "active_cooldowns": len(self.symbol_cooldowns),
            "daily_attempts": dict(self.daily_attempt_counts),
            "recent_decisions_count": len(self.recent_decisions),
            "last_reset_date": self.last_reset_date.isoformat()
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get processor status."""
        return {
            "running": self.running,
            "shared_library_loaded": self.hybrid_helper is not None,
            "vocabulary_loaded": self.vocabulary is not None,
            "csv_sequence": self.csv_sequence,
            "processing_stats": await self.get_processing_stats()
        }