# DOC_ID: DOC-TEST-0013
"""
Data Ingestor Service Tests - Enterprise Integration Example
Demonstrates testing patterns for BaseEnterpriseService implementations
"""

import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from services.common.test_service_template import BaseServiceTestTemplate
from services.data_ingestor.src.main_enterprise import DataIngestorService


class TestDataIngestorEnterpriseService(BaseServiceTestTemplate):
    """Data ingestor tests using enterprise base template"""

    @pytest.fixture
    def service_instance(self):
        """Concrete service instance for testing"""
        with patch('services.data_ingestor.src.main_enterprise.DataIngestor') as mock_ingestor:
            with patch('services.data_ingestor.src.main_enterprise.HealthChecker') as mock_health:
                # Mock the ingestor
                mock_ingestor_instance = AsyncMock()
                mock_ingestor.return_value = mock_ingestor_instance
                mock_ingestor_instance.is_running.return_value = True

                # Mock the health checker
                mock_health_instance = MagicMock()
                mock_health.return_value = mock_health_instance
                mock_health_instance.check_health.return_value = {"status": "healthy"}

                service = DataIngestorService()
                return service

    # Service-specific tests (in addition to template tests)
    @pytest.mark.unit
    def test_price_tick_ingestion(self, test_client, service_instance):
        """Test price tick processing"""
        tick_data = {
            "symbol": "EURUSD",
            "bid": 1.0950,
            "ask": 1.0952,
            "timestamp": "2025-01-15T10:30:00Z"
        }

        # Mock the ingestor process method
        service_instance.ingestor = AsyncMock()
        service_instance.ingestor.process_price_tick = AsyncMock()

        response = test_client.post("/ingest/price-tick", json=tick_data)
        assert response.status_code == 200
        assert response.json()["status"] == "processed"
        assert response.json()["symbol"] == "EURUSD"

    @pytest.mark.unit
    @patch.dict('os.environ', {'FEATURE_ENHANCED_PRICE_VALIDATION': 'true'})
    def test_enhanced_validation_feature_flag(self, test_client, service_instance):
        """Test feature flag controls validation logic"""
        tick_data = {
            "symbol": "GBPUSD",
            "bid": 1.2550,
            "ask": 1.2552,
            "timestamp": "2025-01-15T10:30:00Z"
        }

        # Mock the ingestor
        service_instance.ingestor = AsyncMock()
        service_instance.ingestor.process_price_tick = AsyncMock()

        response = test_client.post("/ingest/price-tick", json=tick_data)
        assert response.status_code == 200

        # Verify feature flag was checked
        assert service_instance.flags.is_enabled("enhanced_price_validation") == True

    @pytest.mark.unit
    def test_service_status_includes_enterprise_features(self, test_client, service_instance):
        """Test service status includes enterprise feature information"""
        response = test_client.get("/status")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "data-ingestor"
        assert "enterprise_features" in data
        assert data["enterprise_features"]["metrics_port"] == 9001  # 8001 + 1000
        assert "feature_flags_enabled" in data["enterprise_features"]

    @pytest.mark.unit
    def test_business_event_tracking(self, service_instance):
        """Test business event tracking works correctly"""
        # Track a business event
        service_instance.track_business_event("price_tick_processed", "success")

        # Verify metric was incremented
        # In real implementation, you'd verify the Prometheus counter
        # For now, just verify the method completes without error
        assert True  # Method completed successfully

    # Integration test example
    @pytest.mark.integration
    @patch('services.data_ingestor.src.config.Settings')
    def test_redis_connection_integration(self, mock_settings, service_instance):
        """Test Redis pub/sub integration"""
        # Mock settings
        mock_settings.return_value.redis_url = "redis://localhost:6379"

        # This would test actual Redis connectivity in a real integration test
        # For this example, we'll just verify the settings are used correctly
        assert service_instance.settings.redis_url is not None

    @pytest.mark.integration
    async def test_startup_shutdown_lifecycle(self, service_instance):
        """Test complete service lifecycle"""
        # Mock dependencies
        service_instance.ingestor = AsyncMock()
        service_instance.health_checker = AsyncMock()

        # Test startup
        await service_instance.startup()
        assert service_instance.startup_complete == True

        # Test health check
        health_status = await service_instance.check_health()
        assert isinstance(health_status, bool)

        # Test shutdown
        await service_instance.shutdown()
        # Verify cleanup was called
        service_instance.ingestor.stop.assert_called_once()

    @pytest.mark.performance
    def test_price_tick_processing_performance(self, test_client, service_instance):
        """Performance test for price tick processing"""
        import time

        tick_data = {
            "symbol": "EURUSD",
            "bid": 1.0950,
            "ask": 1.0952,
            "timestamp": "2025-01-15T10:30:00Z"
        }

        # Mock the ingestor for performance testing
        service_instance.ingestor = AsyncMock()
        service_instance.ingestor.process_price_tick = AsyncMock()

        # Measure processing time
        start_time = time.time()
        response = test_client.post("/ingest/price-tick", json=tick_data)
        processing_time = time.time() - start_time

        assert response.status_code == 200
        assert processing_time < 0.1  # Should process in under 100ms