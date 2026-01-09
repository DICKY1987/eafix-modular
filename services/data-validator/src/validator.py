# DOC_ID: DOC-SERVICE-0051
"""
Data Validator Core

Implements comprehensive data pipeline validation including schema verification,
data quality checks, business rule validation, and anomaly detection.
"""

import asyncio
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import re
import statistics
import csv
from pathlib import Path

import redis.asyncio as redis
import httpx
import structlog

logger = structlog.get_logger(__name__)


class ValidationStatus(Enum):
    """Validation result status."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


class ValidationSeverity(Enum):
    """Validation failure severity."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ValidationResult:
    """Single validation result."""
    
    rule_name: str
    status: ValidationStatus
    severity: ValidationSeverity
    message: str
    details: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        data['severity'] = self.severity.value
        return data


@dataclass
class DataValidationReport:
    """Comprehensive data validation report."""
    
    validation_id: str
    data_type: str
    schema_version: str
    timestamp: datetime
    data_source: Optional[str] = None
    pipeline_name: Optional[str] = None
    validation_results: List[ValidationResult] = None
    overall_status: ValidationStatus = ValidationStatus.PASSED
    quality_score: float = 1.0
    processing_time_ms: float = 0.0
    data_sample_count: int = 0
    anomalies_detected: int = 0
    
    def __post_init__(self):
        if self.validation_results is None:
            self.validation_results = []
    
    def add_result(self, result: ValidationResult):
        """Add a validation result."""
        self.validation_results.append(result)
        
        # Update overall status
        if result.status == ValidationStatus.FAILED and result.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH]:
            self.overall_status = ValidationStatus.FAILED
        elif result.status == ValidationStatus.WARNING and self.overall_status == ValidationStatus.PASSED:
            self.overall_status = ValidationStatus.WARNING
    
    def calculate_quality_score(self):
        """Calculate data quality score based on validation results."""
        if not self.validation_results:
            self.quality_score = 1.0
            return
        
        total_weight = 0
        weighted_score = 0
        
        severity_weights = {
            ValidationSeverity.CRITICAL: 1.0,
            ValidationSeverity.HIGH: 0.8,
            ValidationSeverity.MEDIUM: 0.6,
            ValidationSeverity.LOW: 0.4,
            ValidationSeverity.INFO: 0.2
        }
        
        for result in self.validation_results:
            weight = severity_weights.get(result.severity, 0.5)
            total_weight += weight
            
            if result.status == ValidationStatus.PASSED:
                weighted_score += weight
            elif result.status == ValidationStatus.WARNING:
                weighted_score += weight * 0.7
            # Failed results add 0 to score
        
        self.quality_score = weighted_score / total_weight if total_weight > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['overall_status'] = self.overall_status.value
        data['validation_results'] = [r.to_dict() for r in self.validation_results]
        return data


class SchemaValidator:
    """Schema validation engine."""
    
    def __init__(self, settings):
        self.settings = settings
    
    def validate_schema(self, data: Dict[str, Any], schema: str) -> List[ValidationResult]:
        """Validate data against schema rules."""
        results = []
        
        validation_rules = self.settings.get_validation_rules(schema)
        if not validation_rules or not self.settings.schema_validation_enabled:
            return results
        
        schema_rules = validation_rules.get("schema_validation", {})
        
        # Check required fields
        required_fields = schema_rules.get("required_fields", [])
        for field in required_fields:
            if field not in data:
                results.append(ValidationResult(
                    rule_name=f"required_field_{field}",
                    status=ValidationStatus.FAILED,
                    severity=ValidationSeverity.HIGH,
                    message=f"Required field '{field}' is missing"
                ))
        
        # Check field types
        field_types = schema_rules.get("field_types", {})
        for field, expected_type in field_types.items():
            if field in data:
                if not self._validate_field_type(data[field], expected_type):
                    results.append(ValidationResult(
                        rule_name=f"field_type_{field}",
                        status=ValidationStatus.FAILED,
                        severity=ValidationSeverity.MEDIUM,
                        message=f"Field '{field}' has invalid type. Expected {expected_type}",
                        details={"actual_value": str(data[field]), "expected_type": expected_type}
                    ))
        
        # Check field constraints
        field_constraints = schema_rules.get("field_constraints", {})
        for field, constraints in field_constraints.items():
            if field in data:
                constraint_results = self._validate_field_constraints(field, data[field], constraints)
                results.extend(constraint_results)
        
        # Check enum values
        enum_values = schema_rules.get("enum_values", {})
        for field, valid_values in enum_values.items():
            if field in data:
                if data[field] not in valid_values:
                    results.append(ValidationResult(
                        rule_name=f"enum_value_{field}",
                        status=ValidationStatus.FAILED,
                        severity=ValidationSeverity.MEDIUM,
                        message=f"Field '{field}' has invalid value. Must be one of: {valid_values}",
                        details={"actual_value": data[field], "valid_values": valid_values}
                    ))
        
        return results
    
    def _validate_field_type(self, value: Any, expected_type: str) -> bool:
        """Validate field type."""
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "number":
            return isinstance(value, (int, float))
        elif expected_type == "integer":
            return isinstance(value, int)
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "datetime":
            # Check if it's a valid ISO datetime string
            if isinstance(value, str):
                try:
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return True
                except ValueError:
                    return False
            return False
        elif expected_type == "object":
            return isinstance(value, dict)
        elif expected_type == "array":
            return isinstance(value, list)
        else:
            return True  # Unknown type, allow
    
    def _validate_field_constraints(self, field_name: str, value: Any, constraints: Dict[str, Any]) -> List[ValidationResult]:
        """Validate field constraints."""
        results = []
        
        # String constraints
        if isinstance(value, str):
            if "min_length" in constraints and len(value) < constraints["min_length"]:
                results.append(ValidationResult(
                    rule_name=f"min_length_{field_name}",
                    status=ValidationStatus.FAILED,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Field '{field_name}' is too short. Minimum length: {constraints['min_length']}"
                ))
            
            if "max_length" in constraints and len(value) > constraints["max_length"]:
                results.append(ValidationResult(
                    rule_name=f"max_length_{field_name}",
                    status=ValidationStatus.FAILED,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Field '{field_name}' is too long. Maximum length: {constraints['max_length']}"
                ))
        
        # Numeric constraints
        if isinstance(value, (int, float)):
            if "min" in constraints and value < constraints["min"]:
                results.append(ValidationResult(
                    rule_name=f"min_value_{field_name}",
                    status=ValidationStatus.FAILED,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Field '{field_name}' is below minimum value: {constraints['min']}"
                ))
            
            if "max" in constraints and value > constraints["max"]:
                results.append(ValidationResult(
                    rule_name=f"max_value_{field_name}",
                    status=ValidationStatus.FAILED,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Field '{field_name}' exceeds maximum value: {constraints['max']}"
                ))
        
        return results


class DataQualityValidator:
    """Data quality validation engine."""
    
    def __init__(self, settings):
        self.settings = settings
        self.historical_data: Dict[str, List[Dict[str, Any]]] = {}
    
    def validate_data_quality(self, data: Dict[str, Any], schema: str) -> List[ValidationResult]:
        """Validate data quality."""
        results = []
        
        validation_rules = self.settings.get_validation_rules(schema)
        if not validation_rules or not self.settings.data_quality_checks_enabled:
            return results
        
        quality_rules = validation_rules.get("data_quality", {})
        
        # Schema-specific quality checks
        if schema == "PriceTick@1.0":
            results.extend(self._validate_price_tick_quality(data, quality_rules))
        elif schema == "IndicatorVector@1.1":
            results.extend(self._validate_indicator_quality(data, quality_rules))
        elif schema == "Signal@1.0":
            results.extend(self._validate_signal_quality(data, quality_rules))
        elif schema == "ExecutionReport@1.0":
            results.extend(self._validate_execution_quality(data, quality_rules))
        
        # Common quality checks
        results.extend(self._validate_timestamp_freshness(data, quality_rules))
        results.extend(self._validate_duplicate_detection(data, schema, quality_rules))
        
        return results
    
    def _validate_price_tick_quality(self, data: Dict[str, Any], rules: Dict[str, Any]) -> List[ValidationResult]:
        """Validate price tick data quality."""
        results = []
        
        bid = data.get("bid")
        ask = data.get("ask")
        
        if bid is not None and ask is not None:
            # Bid-Ask spread validation
            spread = ask - bid
            max_spread = rules.get("bid_ask_spread_max", 0.01)
            
            if spread > max_spread:
                results.append(ValidationResult(
                    rule_name="bid_ask_spread",
                    status=ValidationStatus.FAILED,
                    severity=ValidationSeverity.HIGH,
                    message=f"Bid-Ask spread too large: {spread:.5f} > {max_spread}",
                    details={"spread": spread, "max_allowed": max_spread}
                ))
            
            # Price reasonableness check
            if bid <= 0 or ask <= 0:
                results.append(ValidationResult(
                    rule_name="price_positivity",
                    status=ValidationStatus.FAILED,
                    severity=ValidationSeverity.CRITICAL,
                    message="Price values must be positive"
                ))
            
            # Bid should be less than ask
            if bid >= ask:
                results.append(ValidationResult(
                    rule_name="bid_ask_order",
                    status=ValidationStatus.FAILED,
                    severity=ValidationSeverity.HIGH,
                    message=f"Bid ({bid}) should be less than Ask ({ask})"
                ))
        
        return results
    
    def _validate_indicator_quality(self, data: Dict[str, Any], rules: Dict[str, Any]) -> List[ValidationResult]:
        """Validate indicator data quality."""
        results = []
        
        indicators = data.get("indicators", {})
        
        if isinstance(indicators, dict):
            # Check indicator count
            indicator_count = len(indicators)
            min_count = rules.get("indicator_count_min", 1)
            max_count = rules.get("indicator_count_max", 50)
            
            if indicator_count < min_count:
                results.append(ValidationResult(
                    rule_name="indicator_count_min",
                    status=ValidationStatus.FAILED,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Too few indicators: {indicator_count} < {min_count}"
                ))
            
            if indicator_count > max_count:
                results.append(ValidationResult(
                    rule_name="indicator_count_max",
                    status=ValidationStatus.WARNING,
                    severity=ValidationSeverity.LOW,
                    message=f"Many indicators: {indicator_count} > {max_count}"
                ))
            
            # Check for NaN or infinite values
            if not rules.get("nan_values_allowed", False):
                for name, value in indicators.items():
                    if isinstance(value, float):
                        if value != value:  # NaN check
                            results.append(ValidationResult(
                                rule_name="nan_values",
                                status=ValidationStatus.FAILED,
                                severity=ValidationSeverity.HIGH,
                                message=f"NaN value found in indicator: {name}"
                            ))
                        
                        if not rules.get("infinite_values_allowed", False):
                            if abs(value) == float('inf'):
                                results.append(ValidationResult(
                                    rule_name="infinite_values",
                                    status=ValidationStatus.FAILED,
                                    severity=ValidationSeverity.HIGH,
                                    message=f"Infinite value found in indicator: {name}"
                                ))
        
        # Computation time validation
        comp_time = data.get("computation_time_ms")
        if comp_time is not None:
            max_time = rules.get("computation_time_max_ms", 1000)
            if comp_time > max_time:
                results.append(ValidationResult(
                    rule_name="computation_time",
                    status=ValidationStatus.WARNING,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Computation time too high: {comp_time}ms > {max_time}ms"
                ))
        
        return results
    
    def _validate_signal_quality(self, data: Dict[str, Any], rules: Dict[str, Any]) -> List[ValidationResult]:
        """Validate signal data quality."""
        results = []
        
        confidence = data.get("confidence_score")
        if confidence is not None:
            min_conf = rules.get("confidence_score_min", 0.0)
            max_conf = rules.get("confidence_score_max", 1.0)
            
            if confidence < min_conf or confidence > max_conf:
                results.append(ValidationResult(
                    rule_name="confidence_score_range",
                    status=ValidationStatus.FAILED,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Confidence score out of range: {confidence} not in [{min_conf}, {max_conf}]"
                ))
        
        # Price levels consistency
        if rules.get("price_levels_consistency", False):
            entry_price = data.get("entry_price")
            stop_loss = data.get("stop_loss")
            take_profit = data.get("take_profit")
            direction = data.get("direction")
            
            if all(x is not None for x in [entry_price, stop_loss, take_profit, direction]):
                if direction == "BUY":
                    if stop_loss >= entry_price:
                        results.append(ValidationResult(
                            rule_name="buy_stop_loss_logic",
                            status=ValidationStatus.FAILED,
                            severity=ValidationSeverity.HIGH,
                            message="BUY signal: stop loss should be below entry price"
                        ))
                    
                    if take_profit <= entry_price:
                        results.append(ValidationResult(
                            rule_name="buy_take_profit_logic",
                            status=ValidationStatus.FAILED,
                            severity=ValidationSeverity.HIGH,
                            message="BUY signal: take profit should be above entry price"
                        ))
                
                elif direction == "SELL":
                    if stop_loss <= entry_price:
                        results.append(ValidationResult(
                            rule_name="sell_stop_loss_logic",
                            status=ValidationStatus.FAILED,
                            severity=ValidationSeverity.HIGH,
                            message="SELL signal: stop loss should be above entry price"
                        ))
                    
                    if take_profit >= entry_price:
                        results.append(ValidationResult(
                            rule_name="sell_take_profit_logic",
                            status=ValidationStatus.FAILED,
                            severity=ValidationSeverity.HIGH,
                            message="SELL signal: take profit should be below entry price"
                        ))
        
        return results
    
    def _validate_execution_quality(self, data: Dict[str, Any], rules: Dict[str, Any]) -> List[ValidationResult]:
        """Validate execution report quality."""
        results = []
        
        # Execution latency check
        execution_time = data.get("execution_time_ms") or data.get("latency_ms")
        if execution_time is not None:
            max_latency = rules.get("execution_latency_max_ms", 1000)
            if execution_time > max_latency:
                results.append(ValidationResult(
                    rule_name="execution_latency",
                    status=ValidationStatus.WARNING,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"High execution latency: {execution_time}ms > {max_latency}ms"
                ))
        
        # Slippage validation
        expected_price = data.get("expected_price")
        fill_price = data.get("fill_price")
        
        if expected_price is not None and fill_price is not None:
            slippage_pips = abs(fill_price - expected_price) * 10000  # Assuming 4-digit precision
            max_slippage = rules.get("slippage_max_pips", 5)
            
            if slippage_pips > max_slippage:
                results.append(ValidationResult(
                    rule_name="execution_slippage",
                    status=ValidationStatus.WARNING,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"High slippage: {slippage_pips:.1f} pips > {max_slippage} pips"
                ))
        
        return results
    
    def _validate_timestamp_freshness(self, data: Dict[str, Any], rules: Dict[str, Any]) -> List[ValidationResult]:
        """Validate data timestamp freshness."""
        results = []
        
        timestamp_str = data.get("timestamp")
        if not timestamp_str:
            return results
        
        try:
            data_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            now = datetime.utcnow()
            age_minutes = (now - data_timestamp).total_seconds() / 60
            
            max_age_key = next((k for k in rules.keys() if "freshness" in k), None)
            if max_age_key:
                max_age = rules[max_age_key]
                
                if age_minutes > max_age:
                    results.append(ValidationResult(
                        rule_name="timestamp_freshness",
                        status=ValidationStatus.WARNING,
                        severity=ValidationSeverity.MEDIUM,
                        message=f"Data is stale: {age_minutes:.1f} minutes > {max_age} minutes",
                        details={"age_minutes": age_minutes, "max_age_minutes": max_age}
                    ))
        
        except ValueError as e:
            results.append(ValidationResult(
                rule_name="timestamp_format",
                status=ValidationStatus.FAILED,
                severity=ValidationSeverity.MEDIUM,
                message=f"Invalid timestamp format: {e}"
            ))
        
        return results
    
    def _validate_duplicate_detection(self, data: Dict[str, Any], schema: str, rules: Dict[str, Any]) -> List[ValidationResult]:
        """Check for duplicate data."""
        results = []
        
        if not rules.get("duplicate_detection_enabled", False):
            return results
        
        # Create a hash of the data for duplicate detection
        data_copy = data.copy()
        # Remove timestamp for duplicate detection (same data at different times)
        data_copy.pop("timestamp", None)
        data_hash = hashlib.md5(json.dumps(data_copy, sort_keys=True).encode()).hexdigest()
        
        # Store historical data for duplicate detection
        if schema not in self.historical_data:
            self.historical_data[schema] = []
        
        # Check if this data hash was seen recently (last 100 entries)
        recent_hashes = [item.get("hash") for item in self.historical_data[schema][-100:]]
        
        if data_hash in recent_hashes:
            results.append(ValidationResult(
                rule_name="duplicate_detection",
                status=ValidationStatus.WARNING,
                severity=ValidationSeverity.LOW,
                message="Duplicate data detected",
                details={"data_hash": data_hash}
            ))
        
        # Store this data hash
        self.historical_data[schema].append({
            "hash": data_hash,
            "timestamp": datetime.utcnow()
        })
        
        # Keep only recent entries (last 1000)
        if len(self.historical_data[schema]) > 1000:
            self.historical_data[schema] = self.historical_data[schema][-1000:]
        
        return results


class BusinessRuleValidator:
    """Business rule validation engine."""
    
    def __init__(self, settings):
        self.settings = settings
    
    def validate_business_rules(self, data: Dict[str, Any], schema: str) -> List[ValidationResult]:
        """Validate business rules."""
        results = []
        
        validation_rules = self.settings.get_validation_rules(schema)
        if not validation_rules:
            return results
        
        business_rules = validation_rules.get("business_rules", {})
        
        # Schema-specific business rules
        if schema == "PriceTick@1.0":
            results.extend(self._validate_trading_hours(data, business_rules))
            results.extend(self._validate_currency_pair(data, business_rules))
        elif schema == "Signal@1.0":
            results.extend(self._validate_risk_reward_ratio(data, business_rules))
            results.extend(self._validate_market_conditions(data, business_rules))
        elif schema == "OrderIntent@1.2":
            results.extend(self._validate_position_limits(data, business_rules))
            results.extend(self._validate_risk_limits(data, business_rules))
        elif schema == "ExecutionReport@1.0":
            results.extend(self._validate_execution_rules(data, business_rules))
        
        return results
    
    def _validate_trading_hours(self, data: Dict[str, Any], rules: Dict[str, Any]) -> List[ValidationResult]:
        """Validate trading hours."""
        results = []
        
        if not rules.get("trading_hours_validation", False):
            return results
        
        timestamp_str = data.get("timestamp")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                
                # Simple trading hours check (weekdays only)
                if timestamp.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    results.append(ValidationResult(
                        rule_name="weekend_trading",
                        status=ValidationStatus.WARNING,
                        severity=ValidationSeverity.LOW,
                        message="Trading data received during weekend"
                    ))
            
            except ValueError:
                pass  # Invalid timestamp already caught by schema validation
        
        return results
    
    def _validate_currency_pair(self, data: Dict[str, Any], rules: Dict[str, Any]) -> List[ValidationResult]:
        """Validate currency pair format."""
        results = []
        
        if not rules.get("currency_pair_validation", False):
            return results
        
        symbol = data.get("symbol", "")
        
        # Basic currency pair format validation (6-7 characters)
        if len(symbol) not in [6, 7]:
            results.append(ValidationResult(
                rule_name="currency_pair_format",
                status=ValidationStatus.FAILED,
                severity=ValidationSeverity.MEDIUM,
                message=f"Invalid currency pair format: {symbol}"
            ))
        
        return results
    
    def _validate_risk_reward_ratio(self, data: Dict[str, Any], rules: Dict[str, Any]) -> List[ValidationResult]:
        """Validate risk-reward ratio."""
        results = []
        
        min_ratio = rules.get("risk_reward_ratio_min", 1.0)
        
        entry_price = data.get("entry_price")
        stop_loss = data.get("stop_loss")
        take_profit = data.get("take_profit")
        
        if all(x is not None for x in [entry_price, stop_loss, take_profit]):
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            
            if risk > 0:
                ratio = reward / risk
                if ratio < min_ratio:
                    results.append(ValidationResult(
                        rule_name="risk_reward_ratio",
                        status=ValidationStatus.WARNING,
                        severity=ValidationSeverity.MEDIUM,
                        message=f"Poor risk-reward ratio: {ratio:.2f} < {min_ratio}",
                        details={"ratio": ratio, "minimum_required": min_ratio}
                    ))
        
        return results
    
    def _validate_market_conditions(self, data: Dict[str, Any], rules: Dict[str, Any]) -> List[ValidationResult]:
        """Validate market conditions for signal."""
        results = []
        
        if not rules.get("market_conditions_check", False):
            return results
        
        # Placeholder for market condition validation
        # In practice, this would check volatility, spreads, liquidity, etc.
        
        return results
    
    def _validate_position_limits(self, data: Dict[str, Any], rules: Dict[str, Any]) -> List[ValidationResult]:
        """Validate position size limits."""
        results = []
        
        if not rules.get("position_size_limits", False):
            return results
        
        quantity = data.get("quantity", 0)
        
        # Basic position size validation
        if quantity > 100:  # Example limit
            results.append(ValidationResult(
                rule_name="position_size_limit",
                status=ValidationStatus.WARNING,
                severity=ValidationSeverity.MEDIUM,
                message=f"Large position size: {quantity} lots"
            ))
        
        return results
    
    def _validate_risk_limits(self, data: Dict[str, Any], rules: Dict[str, Any]) -> List[ValidationResult]:
        """Validate risk management limits."""
        results = []
        
        # Placeholder for comprehensive risk limit validation
        # Would check daily loss limits, correlation limits, etc.
        
        return results
    
    def _validate_execution_rules(self, data: Dict[str, Any], rules: Dict[str, Any]) -> List[ValidationResult]:
        """Validate execution business rules."""
        results = []
        
        # Check if execution happened during trading hours
        if rules.get("execution_during_trading_hours", False):
            timestamp_str = data.get("timestamp")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    if timestamp.weekday() >= 5:
                        results.append(ValidationResult(
                            rule_name="execution_trading_hours",
                            status=ValidationStatus.WARNING,
                            severity=ValidationSeverity.LOW,
                            message="Execution occurred outside normal trading hours"
                        ))
                
                except ValueError:
                    pass
        
        return results


class DataValidator:
    """Core data validation engine."""
    
    def __init__(self, settings, metrics):
        self.settings = settings
        self.metrics = metrics
        
        # Initialize validation engines
        self.schema_validator = SchemaValidator(settings)
        self.quality_validator = DataQualityValidator(settings)
        self.business_validator = BusinessRuleValidator(settings)
        
        # Redis client for monitoring events
        self.redis_client: Optional[redis.Redis] = None
        
        # HTTP client for service monitoring
        self.http_client: Optional[httpx.AsyncClient] = None
        
        # Validation results storage
        self.validation_reports: List[DataValidationReport] = []
        self._reports_lock = asyncio.Lock()
        
        # Background monitoring tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        
        self.running = False
    
    async def start(self) -> None:
        """Start the data validator."""
        if self.running:
            return
        
        logger.info("Starting Data Validator")
        
        # Validate configuration
        config_errors = self.settings.validate_configuration()
        if config_errors:
            raise RuntimeError(f"Invalid configuration: {config_errors}")
        
        # Initialize Redis connection
        self.redis_client = redis.from_url(self.settings.redis_url)
        await self.redis_client.ping()
        
        # Initialize HTTP client
        timeout = httpx.Timeout(10.0)
        self.http_client = httpx.AsyncClient(timeout=timeout)
        
        # Start monitoring tasks
        if self.settings.data_quality_monitoring_interval_seconds > 0:
            self.monitoring_tasks.append(
                asyncio.create_task(self._run_data_quality_monitoring())
            )
        
        self.running = True
        logger.info("Data Validator started successfully")
    
    async def stop(self) -> None:
        """Stop the data validator."""
        if not self.running:
            return
        
        logger.info("Stopping Data Validator")
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        # Close connections
        if self.http_client:
            await self.http_client.aclose()
        
        if self.redis_client:
            await self.redis_client.close()
        
        self.running = False
        logger.info("Data Validator stopped")
    
    async def validate_data(self, data: Dict[str, Any], schema: str, 
                           data_source: Optional[str] = None) -> DataValidationReport:
        """Validate data against schema and quality rules."""
        start_time = time.time()
        
        # Create validation report
        report = DataValidationReport(
            validation_id=f"val_{int(time.time() * 1000)}",
            data_type=schema.split('@')[0] if '@' in schema else schema,
            schema_version=schema.split('@')[1] if '@' in schema else "1.0",
            timestamp=datetime.utcnow(),
            data_source=data_source,
            data_sample_count=1
        )
        
        try:
            # Schema validation
            if self.settings.schema_validation_enabled:
                schema_results = self.schema_validator.validate_schema(data, schema)
                for result in schema_results:
                    report.add_result(result)
            
            # Data quality validation
            if self.settings.data_quality_checks_enabled:
                quality_results = self.quality_validator.validate_data_quality(data, schema)
                for result in quality_results:
                    report.add_result(result)
            
            # Business rules validation
            business_results = self.business_validator.validate_business_rules(data, schema)
            for result in business_results:
                report.add_result(result)
            
            # Calculate quality score
            report.calculate_quality_score()
            
            # Record processing time
            report.processing_time_ms = (time.time() - start_time) * 1000
            
            # Store report
            await self._store_validation_report(report)
            
            # Record metrics
            self.metrics.record_data_validation(
                schema,
                report.processing_time_ms / 1000,
                report.overall_status == ValidationStatus.PASSED,
                report.quality_score
            )
            
            logger.debug(
                "Data validation completed",
                validation_id=report.validation_id,
                schema=schema,
                status=report.overall_status.value,
                quality_score=report.quality_score
            )
            
        except Exception as e:
            report.overall_status = ValidationStatus.ERROR
            report.add_result(ValidationResult(
                rule_name="validation_error",
                status=ValidationStatus.ERROR,
                severity=ValidationSeverity.CRITICAL,
                message=f"Validation error: {str(e)}"
            ))
            
            logger.error("Data validation failed", error=str(e), exc_info=True)
            self.metrics.record_error("validation_error")
        
        return report
    
    async def validate_csv_file(self, file_path: Path) -> DataValidationReport:
        """Validate CSV file integrity and content."""
        start_time = time.time()
        
        report = DataValidationReport(
            validation_id=f"csv_val_{int(time.time() * 1000)}",
            data_type="CSV_FILE",
            schema_version="1.0",
            timestamp=datetime.utcnow(),
            data_source=str(file_path)
        )
        
        try:
            if not file_path.exists():
                report.add_result(ValidationResult(
                    rule_name="file_exists",
                    status=ValidationStatus.FAILED,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"File does not exist: {file_path}"
                ))
                return report
            
            # File size check
            file_size = file_path.stat().st_size
            if file_size == 0:
                report.add_result(ValidationResult(
                    rule_name="file_size",
                    status=ValidationStatus.FAILED,
                    severity=ValidationSeverity.HIGH,
                    message="File is empty"
                ))
                return report
            
            # Read and validate CSV content
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    csv_reader = csv.reader(f)
                    headers = next(csv_reader)
                    row_count = sum(1 for _ in csv_reader)
                    
                    report.data_sample_count = row_count
                    
                    # Check for required headers (if specified in filename)
                    if "checksum_sha256" in headers:
                        report.add_result(ValidationResult(
                            rule_name="checksum_column_present",
                            status=ValidationStatus.PASSED,
                            severity=ValidationSeverity.INFO,
                            message="Checksum column found"
                        ))
                    
                    # Row count validation
                    if row_count == 0:
                        report.add_result(ValidationResult(
                            rule_name="csv_empty",
                            status=ValidationStatus.WARNING,
                            severity=ValidationSeverity.MEDIUM,
                            message="CSV file contains no data rows"
                        ))
                    elif row_count > 100000:
                        report.add_result(ValidationResult(
                            rule_name="csv_large",
                            status=ValidationStatus.WARNING,
                            severity=ValidationSeverity.LOW,
                            message=f"Large CSV file: {row_count} rows"
                        ))
                
                except csv.Error as e:
                    report.add_result(ValidationResult(
                        rule_name="csv_format",
                        status=ValidationStatus.FAILED,
                        severity=ValidationSeverity.HIGH,
                        message=f"CSV format error: {e}"
                    ))
        
        except Exception as e:
            report.add_result(ValidationResult(
                rule_name="csv_validation_error",
                status=ValidationStatus.ERROR,
                severity=ValidationSeverity.CRITICAL,
                message=f"CSV validation error: {e}"
            ))
        
        report.processing_time_ms = (time.time() - start_time) * 1000
        report.calculate_quality_score()
        
        await self._store_validation_report(report)
        
        return report
    
    async def _run_data_quality_monitoring(self) -> None:
        """Run continuous data quality monitoring."""
        try:
            while self.running:
                try:
                    await self._monitor_data_sources()
                    await asyncio.sleep(self.settings.data_quality_monitoring_interval_seconds)
                    
                except Exception as e:
                    logger.error("Data quality monitoring cycle failed", error=str(e))
                    await asyncio.sleep(10)
                    
        except asyncio.CancelledError:
            logger.info("Data quality monitoring cancelled")
        except Exception as e:
            logger.error("Data quality monitoring failed", error=str(e))
    
    async def _monitor_data_sources(self) -> None:
        """Monitor configured data sources."""
        for source_name, source_config in self.settings.monitored_data_sources.items():
            try:
                endpoint = source_config["endpoint"]
                
                # Check service health
                health_response = await self.http_client.get(f"{endpoint}/healthz")
                
                if health_response.status_code != 200:
                    self.metrics.record_data_source_health(source_name, False)
                    logger.warning(
                        "Data source unhealthy",
                        source=source_name,
                        status_code=health_response.status_code
                    )
                else:
                    self.metrics.record_data_source_health(source_name, True)
                
            except Exception as e:
                self.metrics.record_data_source_health(source_name, False)
                logger.error(
                    "Data source monitoring failed",
                    source=source_name,
                    error=str(e)
                )
    
    async def _store_validation_report(self, report: DataValidationReport) -> None:
        """Store validation report."""
        async with self._reports_lock:
            self.validation_reports.append(report)
            
            # Keep only recent reports based on retention policy
            retention_cutoff = datetime.utcnow() - timedelta(hours=self.settings.validation_results_retention_hours)
            self.validation_reports = [
                r for r in self.validation_reports
                if r.timestamp > retention_cutoff
            ]
    
    # Public API methods
    
    async def get_validation_reports(self, limit: int = 100, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent validation reports."""
        async with self._reports_lock:
            reports = self.validation_reports[-limit:]
            
            if schema:
                reports = [r for r in reports if f"{r.data_type}@{r.schema_version}" == schema]
            
            return [r.to_dict() for r in reports]
    
    async def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary statistics."""
        async with self._reports_lock:
            if not self.validation_reports:
                return {
                    "total_validations": 0,
                    "average_quality_score": 0.0,
                    "validation_failure_rate": 0.0
                }
            
            total_validations = len(self.validation_reports)
            passed_validations = sum(1 for r in self.validation_reports if r.overall_status == ValidationStatus.PASSED)
            avg_quality_score = sum(r.quality_score for r in self.validation_reports) / total_validations
            
            return {
                "total_validations": total_validations,
                "passed_validations": passed_validations,
                "failed_validations": total_validations - passed_validations,
                "validation_success_rate": passed_validations / total_validations,
                "average_quality_score": avg_quality_score,
                "validation_failure_rate": 1 - (passed_validations / total_validations)
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get data validator status."""
        async with self._reports_lock:
            report_count = len(self.validation_reports)
        
        return {
            "running": self.running,
            "monitored_schemas": len(self.settings.validation_rules),
            "monitored_data_sources": len(self.settings.monitored_data_sources),
            "validation_reports_stored": report_count,
            "configuration": self.settings.get_validation_config()
        }