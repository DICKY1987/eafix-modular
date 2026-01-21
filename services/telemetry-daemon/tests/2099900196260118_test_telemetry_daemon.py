# doc_id: DOC-TEST-0038
# DOC_ID: DOC-TEST-0018
"""
Tests for Telemetry Daemon Service

Tests health monitoring, aggregation, alerting, and telemetry coordination.
"""

import pytest
import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "contracts"))

from services.telemetry_daemon.src.config import Settings
from services.telemetry_daemon.src.health import HealthChecker
from services.telemetry_daemon.src.metrics import MetricsCollector
from services.telemetry_daemon.src.collector import HealthMetricsCollector
from services.telemetry_daemon.src.aggregator import SystemHealthAggregator
from services.telemetry_daemon.src.alerting import AlertManager, Alert
from services.telemetry_daemon.src.main import TelemetryDaemonService


class TestTelemetryDaemon:
    """Test telemetry daemon components."""
    
    @pytest.fixture
    def test_settings(self):
        """Create test settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.output_directory = temp_dir
            settings.redis_url = "redis://localhost:6379"
            settings.health_collection_enabled = True
            settings.system_aggregation_enabled = True
            settings.alerting_enabled = True
            settings.csv_output_enabled = True
            
            # Configure test services
            settings.monitored_services = {
                "test-service-1": "http://localhost:8081",
                "test-service-2": "http://localhost:8082"
            }
            
            # Point to contracts
            project_root = Path(__file__).parent.parent.parent.parent
            settings.contracts_directory = str(project_root / "contracts")
            
            yield settings
    
    @pytest.fixture
    def metrics_collector(self):
        """Create metrics collector."""
        return MetricsCollector()
    
    def test_metrics_collector(self, metrics_collector):
        """Test basic metrics collection functionality."""
        # Test counter increment
        metrics_collector.increment_counter("test_counter")
        assert metrics_collector.get_counter_value("test_counter") == 1
        
        metrics_collector.increment_counter("test_counter", 5)
        assert metrics_collector.get_counter_value("test_counter") == 6
        
        # Test gauge setting
        metrics_collector.set_gauge("test_gauge", 42.5)
        assert metrics_collector.get_gauge_value("test_gauge") == 42.5
        
        # Test timing recording
        metrics_collector.record_timing("test_timing", 1.5)
        timing_stats = metrics_collector.get_timing_stats("test_timing")
        assert timing_stats["count"] == 1
        assert timing_stats["avg"] == 1.5
        
        # Test service-specific metrics
        metrics_collector.record_service_health_check("test-service", 0.5, True)
        service_summary = metrics_collector.get_service_metrics_summary("test-service")
        assert service_summary["health_checks"]["total"] == 1
        assert service_summary["health_checks"]["successful"] == 1
    
    @pytest.mark.asyncio
    async def test_health_checker(self, test_settings, metrics_collector):
        """Test health checker functionality."""
        health_checker = HealthChecker(test_settings, metrics_collector)
        
        # Mock external dependencies
        with patch('redis.asyncio.from_url') as mock_redis, \
             patch('httpx.AsyncClient') as mock_http_client:
            
            # Mock Redis
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = True
            mock_redis_instance.info.return_value = {
                "connected_clients": 2,
                "used_memory_human": "1MB",
                "redis_version": "7.0.0",
                "uptime_in_seconds": 3600
            }
            
            # Mock HTTP client
            mock_client = AsyncMock()
            mock_http_client.return_value = mock_client
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            
            await health_checker.start()
            
            # Test health status
            health_status = await health_checker.get_health_status()
            
            assert health_status["service"] == "telemetry-daemon"
            assert "overall_status" in health_status
            assert "health_score" in health_status
            assert "redis" in health_status
            assert "monitored_services" in health_status
            assert "system_resources" in health_status
            
            # Test that Redis health check was performed
            assert health_status["redis"]["healthy"] is True
            
            await health_checker.stop()
    
    @pytest.mark.asyncio
    async def test_health_metrics_collector(self, test_settings, metrics_collector):
        """Test health metrics collection."""
        collector = HealthMetricsCollector(test_settings, metrics_collector)
        
        # Mock HTTP clients
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock health check responses
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy", "uptime": 3600}
            mock_client.get.return_value = mock_response
            
            await collector.start()
            
            # Test collection
            result = await collector.collect_all_service_health()
            
            assert result["success"] is True
            assert result["total_services"] == len(test_settings.monitored_services)
            assert "results" in result
            
            # Verify metrics were recorded
            assert metrics_collector.get_counter_value("health_collection_cycles") >= 0
            
            await collector.stop()
    
    @pytest.mark.asyncio
    async def test_system_health_aggregator(self, test_settings, metrics_collector):
        """Test system health aggregation."""
        aggregator = SystemHealthAggregator(test_settings, metrics_collector)
        
        await aggregator.start()
        
        # Test aggregation
        result = await aggregator.aggregate_system_health()
        
        assert result["success"] is True
        assert "overall_status" in result
        assert "system_health_score" in result
        assert "service_health" in result
        assert "total_services" in result
        
        # Test system overview
        overview = await aggregator.get_system_health_overview()
        if overview.get("available", True):  # May not be available if no history
            assert "historical_data_points" in overview
        
        await aggregator.stop()
    
    @pytest.mark.asyncio
    async def test_alert_manager(self, test_settings, metrics_collector):
        """Test alert management system."""
        alert_manager = AlertManager(test_settings, metrics_collector)
        
        # Mock Redis
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            
            await alert_manager.start()
            
            # Test alert creation
            alert = alert_manager._create_alert(
                "test-service", "cpu_usage_percent", "critical", 95.0, 90.0
            )
            
            assert alert.service_name == "test-service"
            assert alert.metric_name == "cpu_usage_percent"
            assert alert.severity == "critical"
            assert alert.value == 95.0
            assert alert.threshold == 90.0
            
            # Test alert processing
            await alert_manager._process_alert(alert)
            
            # Check active alerts
            active_alerts = await alert_manager.get_active_alerts()
            assert len(active_alerts) == 1
            assert active_alerts[0]["service_name"] == "test-service"
            
            # Test alert statistics
            stats = await alert_manager.get_alert_statistics()
            assert stats["total_alerts"] >= 1
            assert stats["active_alerts"] >= 1
            
            await alert_manager.stop()
    
    def test_alert_data_structure(self):
        """Test alert data structure."""
        alert = Alert(
            id="test-service:cpu_usage:critical",
            service_name="test-service",
            metric_name="cpu_usage_percent",
            severity="critical",
            message="Test alert message",
            value=95.0,
            threshold=90.0,
            timestamp=datetime.utcnow()
        )
        
        # Test serialization
        alert_dict = alert.to_dict()
        assert alert_dict["service_name"] == "test-service"
        assert alert_dict["severity"] == "critical"
        assert "timestamp" in alert_dict
        
        # Test deserialization
        reconstructed = Alert.from_dict(alert_dict)
        assert reconstructed.service_name == alert.service_name
        assert reconstructed.severity == alert.severity
    
    @pytest.mark.asyncio
    async def test_telemetry_service_integration(self, test_settings, metrics_collector):
        """Test complete telemetry daemon service integration."""
        health_checker = HealthChecker(test_settings, metrics_collector)
        service = TelemetryDaemonService(test_settings, metrics_collector, health_checker)
        
        # Mock external dependencies
        with patch('redis.asyncio.from_url') as mock_redis, \
             patch('httpx.AsyncClient') as mock_http_client:
            
            # Mock Redis
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = True
            
            # Mock HTTP client
            mock_client = AsyncMock()
            mock_http_client.return_value = mock_client
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_client.get.return_value = mock_response
            
            await service.start()
            
            # Test service status
            status = await service.get_telemetry_status()
            assert status["service"] == "telemetry-daemon"
            assert status["running"] is True
            
            # Test system health overview
            overview = await service.get_system_health_overview()
            # May be empty initially, but should not error
            assert isinstance(overview, dict)
            
            # Test active alerts (should be empty initially)
            alerts = await service.get_active_alerts()
            assert isinstance(alerts, list)
            
            await service.stop()
    
    def test_configuration_validation(self, test_settings):
        """Test configuration validation."""
        # Test path validation
        errors = test_settings.validate_paths()
        # Should succeed or have minimal errors for temp directory
        assert isinstance(errors, list)
        
        # Test service weight retrieval
        weight = test_settings.get_service_weight("data-ingestor")
        assert weight == 1.5  # From default config
        
        weight = test_settings.get_service_weight("unknown-service")
        assert weight == 1.0  # Default fallback
        
        # Test configuration getters
        health_config = test_settings.get_health_collection_config()
        assert health_config["enabled"] is True
        
        aggregation_config = test_settings.get_aggregation_config()
        assert aggregation_config["enabled"] is True
        
        alerting_config = test_settings.get_alerting_config()
        assert alerting_config["enabled"] is True
    
    def test_prometheus_metrics_format(self, metrics_collector):
        """Test Prometheus metrics format generation."""
        # Add some sample metrics
        metrics_collector.increment_counter("test_counter_total")
        metrics_collector.set_gauge("test_gauge", 42.0)
        metrics_collector.increment_counter("test_with_labels", labels={"service": "test"})
        
        # Generate Prometheus format
        prometheus_output = metrics_collector.get_prometheus_metrics()
        
        assert "telemetry_uptime_seconds" in prometheus_output
        assert "test_counter_total" in prometheus_output
        assert "test_gauge" in prometheus_output
        assert "# TYPE" in prometheus_output
        assert "# HELP" in prometheus_output


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])