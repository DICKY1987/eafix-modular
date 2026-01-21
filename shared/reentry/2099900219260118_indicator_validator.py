# doc_id: DOC-SERVICE-0195
# DOC_ID: DOC-SERVICE-0105
"""
Indicator Record Validator

Validates indicator records against JSON schema specifications.
Works with the contracts validation system for comprehensive checking.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class IndicatorValidator:
    """Validates indicator records against schema and business rules."""
    
    def __init__(self, schema_path: Optional[Path] = None):
        """Initialize validator with schema path."""
        if schema_path is None:
            # Default to contracts schema
            contracts_dir = Path(__file__).parent.parent.parent / "contracts" / "schemas" / "json"
            schema_path = contracts_dir / "indicator_record.schema.json"
        
        self.schema_path = Path(schema_path)
        self.schema: Optional[Dict[str, Any]] = None
        self.load_schema()
    
    def load_schema(self) -> None:
        """Load indicator record JSON schema."""
        try:
            if self.schema_path.exists():
                with open(self.schema_path, 'r') as f:
                    self.schema = json.load(f)
                logger.debug(f"Loaded indicator schema from {self.schema_path}")
            else:
                logger.warning(f"Schema file not found: {self.schema_path}")
        except Exception as e:
            logger.error(f"Failed to load indicator schema: {e}")
    
    def validate_indicator_id(self, indicator_id: str) -> Tuple[bool, List[str]]:
        """
        Validate indicator ID format and conventions.
        
        Args:
            indicator_id: Indicator ID to validate
            
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Check minimum length
        if len(indicator_id) < 3:
            errors.append("IndicatorID must be at least 3 characters long")
        
        # Check pattern (uppercase, alphanumeric, underscores)
        import re
        if not re.match(r'^[A-Z0-9_]+$', indicator_id):
            errors.append("IndicatorID must contain only uppercase letters, numbers, and underscores")
        
        # Check for double underscores
        if '__' in indicator_id:
            errors.append("IndicatorID cannot contain double underscores")
        
        # Check starts and ends properly
        if indicator_id.startswith('_') or indicator_id.endswith('_'):
            errors.append("IndicatorID cannot start or end with underscore")
        
        # Check common naming conventions
        if indicator_id.lower() == indicator_id:
            errors.append("IndicatorID should be uppercase (UPPER_SNAKE_CASE)")
        
        return len(errors) == 0, errors
    
    def validate_output_type(self, output_type: str, thresholds: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate output type matches threshold configuration.
        
        Args:
            output_type: Output type string
            thresholds: Threshold configuration
            
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        valid_output_types = [
            "z_score", "probability_0_1", "state_enum", "boolean", 
            "raw_value", "scalar_0_100", "pips", "percent"
        ]
        
        if output_type not in valid_output_types:
            errors.append(f"Invalid output type: {output_type}. Must be one of: {valid_output_types}")
        
        # Check threshold compatibility
        threshold_kind = thresholds.get("kind", "")
        
        if output_type == "z_score" and threshold_kind != "zscore":
            errors.append("z_score output type should use zscore threshold kind")
        
        if output_type in ["scalar_0_100", "probability_0_1"] and threshold_kind != "band":
            errors.append(f"{output_type} output type should use band threshold kind")
        
        if output_type == "percent" and threshold_kind != "percent_change":
            errors.append("percent output type should use percent_change threshold kind")
        
        return len(errors) == 0, errors
    
    def validate_threshold_configuration(self, thresholds: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate threshold configuration structure and values.
        
        Args:
            thresholds: Threshold configuration dictionary
            
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        threshold_kind = thresholds.get("kind", "")
        valid_kinds = ["zscore", "band", "percent_change"]
        
        if threshold_kind not in valid_kinds:
            errors.append(f"Invalid threshold kind: {threshold_kind}. Must be one of: {valid_kinds}")
            return False, errors
        
        # Validate zscore thresholds
        if threshold_kind == "zscore":
            if "gte" not in thresholds:
                errors.append("zscore threshold must have 'gte' value")
            
            gte = thresholds.get("gte")
            lte = thresholds.get("lte")
            
            if gte is not None and not isinstance(gte, (int, float)):
                errors.append("gte must be a number")
            
            if lte is not None:
                if not isinstance(lte, (int, float)):
                    errors.append("lte must be a number")
                elif gte is not None and lte <= gte:
                    errors.append("lte must be greater than gte")
        
        # Validate band thresholds
        elif threshold_kind == "band":
            required_fields = ["upper", "lower"]
            for field in required_fields:
                if field not in thresholds:
                    errors.append(f"band threshold must have '{field}' value")
            
            upper = thresholds.get("upper")
            lower = thresholds.get("lower")
            
            if upper is not None and lower is not None:
                if not isinstance(upper, (int, float)) or not isinstance(lower, (int, float)):
                    errors.append("upper and lower must be numbers")
                elif upper <= lower:
                    errors.append("upper must be greater than lower")
        
        # Validate percent_change thresholds
        elif threshold_kind == "percent_change":
            if "abs_change_gte" not in thresholds:
                errors.append("percent_change threshold must have 'abs_change_gte' value")
            
            if "window" not in thresholds:
                errors.append("percent_change threshold must have 'window' configuration")
            else:
                window_errors = self.validate_time_window(thresholds["window"])
                errors.extend(window_errors)
        
        # Validate common optional fields
        hysteresis = thresholds.get("hysteresis", 0.0)
        if not isinstance(hysteresis, (int, float)) or hysteresis < 0:
            errors.append("hysteresis must be non-negative number")
        
        persistence = thresholds.get("persistence_bars", 0)
        if not isinstance(persistence, int) or persistence < 0:
            errors.append("persistence_bars must be non-negative integer")
        
        return len(errors) == 0, errors
    
    def validate_time_window(self, window: Dict[str, Any]) -> List[str]:
        """
        Validate time window configuration for percent_change thresholds.
        
        Args:
            window: Time window configuration
            
        Returns:
            List of validation errors
        """
        errors = []
        
        required_fields = ["tz", "start", "end", "days"]
        for field in required_fields:
            if field not in window:
                errors.append(f"Time window must have '{field}' field")
        
        # Validate time format
        import re
        time_pattern = r'^\d{2}:\d{2}$'
        
        start_time = window.get("start", "")
        if not re.match(time_pattern, start_time):
            errors.append(f"start time must be HH:MM format, got: {start_time}")
        
        end_time = window.get("end", "")
        if not re.match(time_pattern, end_time):
            errors.append(f"end time must be HH:MM format, got: {end_time}")
        
        # Validate days
        days = window.get("days", [])
        if not isinstance(days, list) or len(days) == 0:
            errors.append("days must be non-empty list")
        else:
            valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            for day in days:
                if day not in valid_days:
                    errors.append(f"Invalid day: {day}. Must be one of: {valid_days}")
        
        return errors
    
    def validate_inputs_configuration(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate inputs configuration.
        
        Args:
            inputs: Inputs configuration dictionary
            
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate symbol_scope if present
        symbol_scope = inputs.get("symbol_scope")
        if symbol_scope is not None:
            if not isinstance(symbol_scope, list):
                errors.append("symbol_scope must be a list")
            else:
                for symbol in symbol_scope:
                    if not isinstance(symbol, str) or len(symbol) < 6:
                        errors.append(f"Invalid symbol in symbol_scope: {symbol}")
        
        # Validate timeframe format
        timeframe = inputs.get("timeframe")
        if timeframe is not None:
            valid_timeframes = ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"]
            if timeframe not in valid_timeframes:
                errors.append(f"Invalid timeframe: {timeframe}. Should be one of: {valid_timeframes}")
        
        # Validate weights if present
        weights = inputs.get("weights")
        if weights is not None:
            if not isinstance(weights, dict):
                errors.append("weights must be a dictionary")
            else:
                for key, value in weights.items():
                    if not isinstance(value, (int, float)):
                        errors.append(f"weight for {key} must be a number")
        
        return len(errors) == 0, errors
    
    def validate_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate complete indicator record.
        
        Args:
            record: Indicator record dictionary
            
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        required_fields = [
            "IndicatorID", "Concept", "Indicator_Computation", 
            "Signal_Logic", "OutputType", "Thresholds", "Inputs"
        ]
        
        for field in required_fields:
            if field not in record:
                errors.append(f"Missing required field: {field}")
        
        # Validate specific fields
        if "IndicatorID" in record:
            id_valid, id_errors = self.validate_indicator_id(record["IndicatorID"])
            errors.extend(id_errors)
        
        if "OutputType" in record and "Thresholds" in record:
            output_valid, output_errors = self.validate_output_type(
                record["OutputType"], record["Thresholds"]
            )
            errors.extend(output_errors)
        
        if "Thresholds" in record:
            threshold_valid, threshold_errors = self.validate_threshold_configuration(record["Thresholds"])
            errors.extend(threshold_errors)
        
        if "Inputs" in record:
            inputs_valid, inputs_errors = self.validate_inputs_configuration(record["Inputs"])
            errors.extend(inputs_errors)
        
        # Validate string field lengths
        string_fields = ["Concept", "Indicator_Computation", "Signal_Logic"]
        for field in string_fields:
            if field in record:
                value = record[field]
                if not isinstance(value, str) or len(value) < 3:
                    errors.append(f"{field} must be a string with at least 3 characters")
        
        return len(errors) == 0, errors
    
    def validate_record_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate indicator record from JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            (is_valid, list_of_errors)
        """
        try:
            with open(file_path, 'r') as f:
                record = json.load(f)
            
            return self.validate_record(record)
            
        except Exception as e:
            return False, [f"Failed to load record file: {e}"]