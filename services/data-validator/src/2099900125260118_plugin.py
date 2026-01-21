# doc_id: DOC-SERVICE-0133
# DOC_ID: DOC-ARCH-0109
"""
Data Validator Plugin
Validates incoming data for integrity and quality
"""

from typing import Dict, Any, Optional
import structlog

from shared.plugin_interface import BasePlugin, PluginMetadata


logger = structlog.get_logger(__name__)


class DataValidatorPlugin(BasePlugin):
    """Data validator for quality checks"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="data-validator",
            version="1.0.0",
            description="Data validation and quality checks",
            author="EAFIX Team",
            dependencies=["data-ingestor"],
        )
        super().__init__(metadata)
        self._validation_stats = {
            "total": 0,
            "passed": 0,
            "failed": 0
        }
    
    async def _on_initialize(self) -> None:
        """Initialize the data validator"""
        # Subscribe to price ticks for validation
        self._context.subscribe("price_tick", self._validate_price_tick)
        
        logger.info("Data validator initialized")
    
    async def _on_start(self) -> None:
        """Start the data validator"""
        logger.info("Starting data validator")
    
    async def _on_stop(self) -> None:
        """Stop the data validator"""
        logger.info("Stopping data validator", stats=self._validation_stats)
    
    def _validate_price_tick(self, event_type: str, data: Any, source: str) -> None:
        """Validate price tick data"""
        self._validation_stats["total"] += 1
        
        try:
            # Perform validation checks
            if not isinstance(data, dict):
                raise ValueError("Data must be a dictionary")
            
            required_fields = ["symbol", "price", "timestamp"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate price is positive
            price = data.get("price")
            if not isinstance(price, (int, float)) or price <= 0:
                raise ValueError(f"Invalid price: {price}")
            
            self._validation_stats["passed"] += 1
            
        except Exception as e:
            self._validation_stats["failed"] += 1
            logger.warning(
                "Validation failed",
                error=str(e),
                data=data,
                source=source
            )
            
            # Emit validation failure event
            self.emit_event("validation_failed", {
                "event_type": event_type,
                "error": str(e),
                "source": source
            })
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        health = await super().health_check()
        health["validation_stats"] = self._validation_stats
        
        # Calculate failure rate
        if self._validation_stats["total"] > 0:
            failure_rate = self._validation_stats["failed"] / self._validation_stats["total"]
            health["failure_rate"] = round(failure_rate, 4)
            
            # Mark unhealthy if failure rate > 10%
            if failure_rate > 0.1:
                health["status"] = "degraded"
        
        return health


plugin_class = DataValidatorPlugin
