#!/usr/bin/env python3
# doc_id: DOC-SERVICE-0150
# DOC_ID: DOC-SERVICE-0044
"""
Data Ingestor Service - Enterprise Integration Example
Demonstrates how to integrate existing service with BaseEnterpriseService
"""

import asyncio
import os
from services.common.base_service import BaseEnterpriseService

from .ingestor import DataIngestor
from .config import Settings
from .health import HealthChecker


class DataIngestorService(BaseEnterpriseService):
    """Data ingestion service with enterprise capabilities"""

    def __init__(self):
        super().__init__("data-ingestor", port=8001)

        # Service-specific components
        self.settings = Settings()
        self.health_checker = HealthChecker()
        self.ingestor = None

        # Add service endpoints
        self._setup_service_endpoints()

    def _setup_service_endpoints(self):
        """Setup data ingestor specific endpoints"""

        @self.app.post("/ingest/price-tick")
        async def ingest_price_tick(tick_data: dict):
            """Ingest price tick data with enterprise monitoring"""

            # Check feature flag for enhanced validation
            if self.flags.is_enabled("enhanced_price_validation"):
                # Enhanced validation logic would go here
                self.logger.info("using_enhanced_price_validation",
                               symbol=tick_data.get("symbol"))

            try:
                # Process the price tick
                await self.ingestor.process_price_tick(tick_data)

                # Track business metric
                self.track_business_event("price_tick_processed")

                return {"status": "processed", "symbol": tick_data.get("symbol")}

            except Exception as e:
                self.track_business_event("price_tick_failed", "error")
                self.logger.error("price_tick_processing_failed",
                                error=str(e),
                                symbol=tick_data.get("symbol"))
                raise

        @self.app.get("/status")
        async def service_status():
            """Service status with enterprise monitoring"""
            return {
                "service": self.service_name,
                "version": "1.0.0",
                "status": "running",
                "config": {
                    "redis_url": self.settings.redis_url,
                    "log_level": self.settings.log_level
                },
                "enterprise_features": {
                    "metrics_port": self.port + 1000,
                    "feature_flags_enabled": len([k for k in os.environ.keys() if k.startswith("FEATURE_")]),
                    "health_monitoring": True
                }
            }

    # Required implementations from BaseEnterpriseService
    async def startup(self):
        """Service-specific startup logic"""
        self.logger.info("initializing_data_ingestor_components")

        # Initialize the data ingestor
        self.ingestor = DataIngestor(self.settings, self.metrics)
        await self.ingestor.start()

        self.logger.info("data_ingestor_startup_complete")

    async def shutdown(self):
        """Service-specific shutdown logic"""
        self.logger.info("shutting_down_data_ingestor")

        if self.ingestor:
            await self.ingestor.stop()

        self.logger.info("data_ingestor_shutdown_complete")

    async def check_health(self) -> bool:
        """Service-specific health check logic"""
        try:
            # Use existing health checker
            health_status = await self.health_checker.check_health()

            # Additional checks specific to data ingestion
            ingestor_healthy = self.ingestor and self.ingestor.is_running()

            return (health_status["status"] == "healthy" and ingestor_healthy)

        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            return False


def main():
    """Main entry point for enterprise data ingestor"""
    import uvicorn

    service = DataIngestorService()
    uvicorn.run(service.app, host="0.0.0.0", port=service.port)


if __name__ == "__main__":
    main()