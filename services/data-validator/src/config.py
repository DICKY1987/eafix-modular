"""
Data Validator Configuration

Configuration for data pipeline validation, schema verification,
and data quality monitoring across EAFIX services.
"""

from pathlib import Path
from pydantic import BaseSettings, Field
from typing import List, Dict, Any, Optional, Set


class Settings(BaseSettings):
    """Data Validator service settings."""
    
    # Basic service configuration
    service_port: int = Field(8095, description="Service HTTP port")
    log_level: str = Field("INFO", description="Logging level")
    debug_mode: bool = Field(False, description="Enable debug mode")
    
    # Redis configuration
    redis_url: str = Field(
        "redis://localhost:6379", 
        description="Redis connection URL"
    )
    
    # Data validation configuration
    data_validation_enabled: bool = Field(
        True,
        description="Enable data validation functionality"
    )
    
    schema_validation_enabled: bool = Field(
        True,
        description="Enable schema validation"
    )
    
    data_quality_checks_enabled: bool = Field(
        True,
        description="Enable data quality checks"
    )
    
    pipeline_validation_enabled: bool = Field(
        True,
        description="Enable end-to-end pipeline validation"
    )
    
    # Validation rules configuration
    validation_rules: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "PriceTick@1.0": {
                "schema_validation": {
                    "required_fields": ["symbol", "bid", "ask", "timestamp"],
                    "field_types": {
                        "symbol": "string",
                        "bid": "number",
                        "ask": "number",
                        "timestamp": "datetime",
                        "volume": "number"
                    },
                    "field_constraints": {
                        "symbol": {"min_length": 3, "max_length": 8},
                        "bid": {"min": 0, "max": 10000},
                        "ask": {"min": 0, "max": 10000},
                        "volume": {"min": 0}
                    }
                },
                "data_quality": {
                    "bid_ask_spread_max": 0.01,  # Maximum 100 pips
                    "price_change_max_percent": 5.0,  # Maximum 5% price change
                    "timestamp_freshness_minutes": 5,  # Data must be within 5 minutes
                    "duplicate_detection_enabled": True
                },
                "business_rules": {
                    "trading_hours_validation": True,
                    "market_closure_check": True,
                    "currency_pair_validation": True
                }
            },
            "IndicatorVector@1.1": {
                "schema_validation": {
                    "required_fields": ["symbol", "indicators", "timestamp", "timeframe"],
                    "field_types": {
                        "symbol": "string",
                        "indicators": "object",
                        "timestamp": "datetime",
                        "timeframe": "string",
                        "computation_time_ms": "number"
                    }
                },
                "data_quality": {
                    "indicator_count_min": 1,
                    "indicator_count_max": 50,
                    "computation_time_max_ms": 1000,
                    "nan_values_allowed": False,
                    "infinite_values_allowed": False
                },
                "business_rules": {
                    "indicator_correlation_check": True,
                    "timeframe_consistency_check": True
                }
            },
            "Signal@1.0": {
                "schema_validation": {
                    "required_fields": ["signal_id", "symbol", "direction", "confidence_score", "timestamp"],
                    "field_types": {
                        "signal_id": "string",
                        "symbol": "string",
                        "direction": "string",
                        "confidence_score": "number",
                        "timestamp": "datetime",
                        "entry_price": "number",
                        "stop_loss": "number",
                        "take_profit": "number"
                    },
                    "enum_values": {
                        "direction": ["BUY", "SELL", "NEUTRAL"]
                    }
                },
                "data_quality": {
                    "confidence_score_min": 0.0,
                    "confidence_score_max": 1.0,
                    "signal_freshness_minutes": 10,
                    "price_levels_consistency": True
                },
                "business_rules": {
                    "risk_reward_ratio_min": 1.0,
                    "stop_loss_validation": True,
                    "market_conditions_check": True
                }
            },
            "OrderIntent@1.2": {
                "schema_validation": {
                    "required_fields": ["order_id", "symbol", "direction", "quantity", "order_type", "timestamp"],
                    "field_types": {
                        "order_id": "string",
                        "symbol": "string",
                        "direction": "string",
                        "quantity": "number",
                        "order_type": "string",
                        "timestamp": "datetime",
                        "price": "number",
                        "stop_loss": "number",
                        "take_profit": "number"
                    }
                },
                "data_quality": {
                    "quantity_min": 0.01,
                    "quantity_max": 1000.0,
                    "risk_validation_passed": True,
                    "account_balance_sufficient": True
                },
                "business_rules": {
                    "position_size_limits": True,
                    "daily_loss_limits": True,
                    "correlation_limits": True
                }
            },
            "ExecutionReport@1.0": {
                "schema_validation": {
                    "required_fields": ["execution_id", "order_id", "symbol", "status", "timestamp"],
                    "field_types": {
                        "execution_id": "string",
                        "order_id": "string",
                        "symbol": "string",
                        "status": "string",
                        "timestamp": "datetime",
                        "fill_price": "number",
                        "fill_quantity": "number"
                    },
                    "enum_values": {
                        "status": ["FILLED", "PARTIAL_FILL", "REJECTED", "CANCELLED", "PENDING"]
                    }
                },
                "data_quality": {
                    "execution_latency_max_ms": 1000,
                    "slippage_max_pips": 5,
                    "fill_price_reasonableness": True
                },
                "business_rules": {
                    "execution_during_trading_hours": True,
                    "fill_price_within_spread": True,
                    "quantity_consistency_check": True
                }
            },
            "CalendarEvent@1.0": {
                "schema_validation": {
                    "required_fields": ["event_id", "currency", "event_name", "scheduled_time", "impact"],
                    "field_types": {
                        "event_id": "string",
                        "currency": "string",
                        "event_name": "string",
                        "scheduled_time": "datetime",
                        "impact": "string",
                        "actual_value": "number",
                        "forecast_value": "number"
                    },
                    "enum_values": {
                        "impact": ["LOW", "MEDIUM", "HIGH"]
                    }
                },
                "data_quality": {
                    "event_timeliness_hours": 24,  # Events should be within 24 hours
                    "currency_code_validation": True,
                    "duplicate_event_check": True
                }
            },
            "ReentryDecision@1.0": {
                "schema_validation": {
                    "required_fields": ["decision_id", "original_trade_id", "decision", "timestamp"],
                    "field_types": {
                        "decision_id": "string",
                        "original_trade_id": "string",
                        "decision": "string",
                        "timestamp": "datetime",
                        "confidence_score": "number",
                        "parameters": "object"
                    },
                    "enum_values": {
                        "decision": ["REENTER", "WAIT", "SKIP"]
                    }
                },
                "data_quality": {
                    "decision_latency_max_minutes": 5,
                    "confidence_threshold": 0.5,
                    "parameter_validation": True
                }
            },
            "HealthMetric@1.0": {
                "schema_validation": {
                    "required_fields": ["service_name", "metric_name", "value", "timestamp"],
                    "field_types": {
                        "service_name": "string",
                        "metric_name": "string",
                        "value": "number",
                        "timestamp": "datetime",
                        "unit": "string",
                        "status": "string"
                    }
                },
                "data_quality": {
                    "metric_freshness_minutes": 2,
                    "value_range_validation": True,
                    "anomaly_detection": True
                }
            }
        },
        description="Validation rules for each data type"
    )
    
    # Pipeline validation configuration
    pipeline_validation_rules: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "price_to_signal_pipeline": {
                "input_schema": "PriceTick@1.0",
                "output_schema": "Signal@1.0",
                "max_latency_ms": 2000,
                "data_transformation_checks": [
                    "price_to_indicator_consistency",
                    "indicator_to_signal_logic",
                    "signal_confidence_calculation"
                ],
                "quality_gates": {
                    "min_data_quality_score": 0.9,
                    "max_processing_time_ms": 1500,
                    "required_indicator_completeness": 0.95
                }
            },
            "signal_to_execution_pipeline": {
                "input_schema": "Signal@1.0",
                "output_schema": "ExecutionReport@1.0",
                "max_latency_ms": 5000,
                "data_transformation_checks": [
                    "signal_to_order_conversion",
                    "risk_management_validation",
                    "execution_result_consistency"
                ],
                "quality_gates": {
                    "min_risk_score": 0.8,
                    "max_execution_slippage_pips": 3,
                    "required_order_fill_rate": 0.95
                }
            },
            "calendar_to_signal_pipeline": {
                "input_schema": "CalendarEvent@1.0",
                "output_schema": "Signal@1.0",
                "max_latency_ms": 1000,
                "data_transformation_checks": [
                    "calendar_event_impact_assessment",
                    "market_condition_evaluation",
                    "signal_generation_logic"
                ],
                "quality_gates": {
                    "min_event_relevance_score": 0.7,
                    "max_signal_generation_time_ms": 500
                }
            }
        },
        description="Pipeline-level validation rules"
    )
    
    # Data quality monitoring
    data_quality_monitoring_interval_seconds: int = Field(
        30,
        gt=0,
        description="Interval for data quality monitoring"
    )
    
    anomaly_detection_enabled: bool = Field(
        True,
        description="Enable anomaly detection"
    )
    
    anomaly_detection_sensitivity: float = Field(
        0.05,  # 5% deviation threshold
        gt=0.0,
        le=1.0,
        description="Anomaly detection sensitivity (0.0 to 1.0)"
    )
    
    # Validation result storage
    validation_results_retention_hours: int = Field(
        72,
        gt=0,
        description="Retention period for validation results"
    )
    
    store_validation_results: bool = Field(
        True,
        description="Store validation results for analysis"
    )
    
    # Alert configuration
    validation_alerts_enabled: bool = Field(
        True,
        description="Enable validation alerts"
    )
    
    critical_validation_failure_threshold: int = Field(
        5,
        gt=0,
        description="Number of critical failures before alerting"
    )
    
    data_quality_degradation_threshold: float = Field(
        0.8,  # Alert if quality drops below 80%
        gt=0.0,
        le=1.0,
        description="Data quality threshold for alerting"
    )
    
    # Performance monitoring
    validation_performance_monitoring: bool = Field(
        True,
        description="Monitor validation performance"
    )
    
    max_validation_time_ms: int = Field(
        100,
        gt=0,
        description="Maximum allowed validation time"
    )
    
    # CSV validation configuration
    csv_validation_enabled: bool = Field(
        True,
        description="Enable CSV file validation"
    )
    
    csv_integrity_checks: List[str] = Field(
        default_factory=lambda: [
            "checksum_validation",
            "schema_compliance",
            "row_count_validation",
            "data_completeness",
            "timestamp_ordering",
            "duplicate_detection"
        ],
        description="CSV integrity checks to perform"
    )
    
    # Service monitoring
    monitored_data_sources: Dict[str, Dict[str, str]] = Field(
        default_factory=lambda: {
            "data-ingestor": {
                "endpoint": "http://localhost:8081",
                "data_types": "PriceTick@1.0"
            },
            "indicator-engine": {
                "endpoint": "http://localhost:8082", 
                "data_types": "IndicatorVector@1.1"
            },
            "signal-generator": {
                "endpoint": "http://localhost:8083",
                "data_types": "Signal@1.0"
            },
            "risk-manager": {
                "endpoint": "http://localhost:8084",
                "data_types": "OrderIntent@1.2"
            },
            "execution-engine": {
                "endpoint": "http://localhost:8085",
                "data_types": "ExecutionReport@1.0"
            },
            "calendar-ingestor": {
                "endpoint": "http://localhost:8086",
                "data_types": "CalendarEvent@1.0,ActiveCalendarSignal@1.0"
            },
            "reentry-engine": {
                "endpoint": "http://localhost:8089",
                "data_types": "ReentryDecision@1.0"
            },
            "telemetry-daemon": {
                "endpoint": "http://localhost:8092",
                "data_types": "HealthMetric@1.0"
            }
        },
        description="Data sources to monitor for validation"
    )
    
    # Output configuration
    output_directory: str = Field(
        "./data/data-validator",
        description="Directory for validation results output"
    )
    
    validation_reports_enabled: bool = Field(
        True,
        description="Generate validation reports"
    )
    
    report_generation_interval_hours: int = Field(
        1,
        gt=0,
        description="Interval for generating validation reports"
    )
    
    # Integration settings
    contracts_directory: str = Field(
        "../../../contracts",
        description="Path to contracts directory"
    )
    
    class Config:
        env_prefix = "DATA_VALIDATOR_"
        env_file = ".env"
    
    def get_output_path(self) -> Path:
        """Get resolved output directory path."""
        return Path(self.output_directory).resolve()
    
    def get_contracts_path(self) -> Path:
        """Get resolved contracts directory path."""
        return Path(self.contracts_directory).resolve()
    
    def get_validation_rules(self, schema: str) -> Optional[Dict[str, Any]]:
        """Get validation rules for a schema."""
        return self.validation_rules.get(schema)
    
    def get_pipeline_validation_rules(self, pipeline_name: str) -> Optional[Dict[str, Any]]:
        """Get pipeline validation rules."""
        return self.pipeline_validation_rules.get(pipeline_name)
    
    def get_all_monitored_schemas(self) -> Set[str]:
        """Get all schemas that are monitored."""
        schemas = set(self.validation_rules.keys())
        
        # Add schemas from data sources
        for source_config in self.monitored_data_sources.values():
            data_types = source_config.get("data_types", "")
            if data_types:
                schemas.update(data_types.split(","))
        
        return schemas
    
    def get_data_sources_for_schema(self, schema: str) -> List[str]:
        """Get data sources that produce a specific schema."""
        sources = []
        
        for source_name, source_config in self.monitored_data_sources.items():
            data_types = source_config.get("data_types", "")
            if schema in data_types.split(","):
                sources.append(source_name)
        
        return sources
    
    def get_validation_config(self) -> Dict[str, Any]:
        """Get validation configuration summary."""
        return {
            "data_validation_enabled": self.data_validation_enabled,
            "schema_validation_enabled": self.schema_validation_enabled,
            "data_quality_checks_enabled": self.data_quality_checks_enabled,
            "pipeline_validation_enabled": self.pipeline_validation_enabled,
            "csv_validation_enabled": self.csv_validation_enabled,
            "anomaly_detection_enabled": self.anomaly_detection_enabled,
            "validation_alerts_enabled": self.validation_alerts_enabled,
            "total_validation_rules": len(self.validation_rules),
            "total_pipeline_rules": len(self.pipeline_validation_rules),
            "monitored_data_sources": len(self.monitored_data_sources)
        }
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return any errors."""
        errors = []
        
        # Validate thresholds
        if self.anomaly_detection_sensitivity <= 0 or self.anomaly_detection_sensitivity > 1:
            errors.append("Invalid anomaly detection sensitivity")
        
        if self.data_quality_degradation_threshold <= 0 or self.data_quality_degradation_threshold > 1:
            errors.append("Invalid data quality threshold")
        
        # Validate time intervals
        if self.data_quality_monitoring_interval_seconds <= 0:
            errors.append("Invalid monitoring interval")
        
        if self.validation_results_retention_hours <= 0:
            errors.append("Invalid retention period")
        
        # Validate validation rules
        for schema, rules in self.validation_rules.items():
            if "schema_validation" not in rules:
                errors.append(f"Schema {schema} missing schema_validation rules")
            
            if "required_fields" not in rules.get("schema_validation", {}):
                errors.append(f"Schema {schema} missing required_fields")
        
        # Validate pipeline rules
        for pipeline, rules in self.pipeline_validation_rules.items():
            required_fields = ["input_schema", "output_schema", "max_latency_ms"]
            for field in required_fields:
                if field not in rules:
                    errors.append(f"Pipeline {pipeline} missing {field}")
        
        return errors