"""
Service Startup Tests

Tests for verifying all EAFIX services start correctly and are healthy.
Validates service discovery, health checks, and readiness.
"""

import pytest
import asyncio
import httpx
import json
from typing import Dict, Any, List


@pytest.mark.integration
@pytest.mark.services_required
class TestServiceStartup:
    """Test service startup and health validation."""
    
    async def test_all_services_start_successfully(
        self, 
        service_manager,
        integration_test_config,
        http_client,
        test_service_client
    ):
        """Test that all required services start and become healthy."""
        expected_services = integration_test_config["expected_services"]
        service_info = {}
        
        # Start all services
        for i, service_name in enumerate(expected_services):
            port = 8093 + i
            service_dir = service_name
            
            # Start service
            info = await service_manager.start_service(
                service_name, 
                port, 
                service_dir,
                timeout=integration_test_config["service_startup_timeout"]
            )
            
            service_info[service_name] = info
            assert info["ready"], f"Service {service_name} failed to become ready"
            assert info["port"] == port
            assert info["endpoint"] == f"http://localhost:{port}"
        
        # Verify all services are running
        for service_name, info in service_info.items():
            health = await test_service_client.get_service_health(info["endpoint"])
            assert health["status"] == "healthy", f"Service {service_name} is not healthy"
            
            readiness = await test_service_client.get_service_readiness(info["endpoint"])
            assert readiness["status"] == "ready", f"Service {service_name} is not ready"
    
    async def test_service_health_endpoints(
        self,
        flow_orchestrator,
        event_gateway,
        data_validator,
        flow_monitor,
        telemetry_daemon,
        test_service_client
    ):
        """Test health endpoints for all services."""
        services = {
            "flow-orchestrator": flow_orchestrator,
            "event-gateway": event_gateway,
            "data-validator": data_validator,
            "flow-monitor": flow_monitor,
            "telemetry-daemon": telemetry_daemon
        }
        
        for service_name, service_info in services.items():
            # Test health endpoint
            health = await test_service_client.get_service_health(service_info["endpoint"])
            
            assert health["status"] == "healthy"
            assert "timestamp" in health
            assert "uptime_seconds" in health
            assert health["service"] == service_name
            
            # Test readiness endpoint
            readiness = await test_service_client.get_service_readiness(service_info["endpoint"])
            
            assert readiness["status"] == "ready"
            assert "dependencies" in readiness
            assert "redis" in readiness["dependencies"]
            assert readiness["dependencies"]["redis"]["status"] == "healthy"
    
    async def test_service_metrics_available(
        self,
        flow_orchestrator,
        event_gateway,
        data_validator,
        flow_monitor,
        telemetry_daemon,
        test_service_client
    ):
        """Test that all services expose Prometheus metrics."""
        services = {
            "flow-orchestrator": flow_orchestrator,
            "event-gateway": event_gateway,
            "data-validator": data_validator,
            "flow-monitor": flow_monitor,
            "telemetry-daemon": telemetry_daemon
        }
        
        for service_name, service_info in services.items():
            metrics = await test_service_client.get_service_metrics(service_info["endpoint"])
            
            assert "service" in metrics
            assert metrics["service"] == service_name
            assert "uptime_seconds" in metrics
            assert "request_count" in metrics
            assert "error_count" in metrics
    
    async def test_redis_connectivity(self, redis_client):
        """Test Redis connectivity from all services."""
        # Test basic Redis operations
        await redis_client.set("test_key", "test_value")
        value = await redis_client.get("test_key")
        assert value == b"test_value"
        
        await redis_client.delete("test_key")
        
        # Test pub/sub functionality
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("test_channel")
        
        await redis_client.publish("test_channel", "test_message")
        
        # Get subscription confirmation and test message
        message = await pubsub.get_message(timeout=1.0)
        if message and message["type"] == "subscribe":
            message = await pubsub.get_message(timeout=1.0)
        
        assert message is not None
        assert message["type"] == "message"
        assert message["data"] == b"test_message"
        
        await pubsub.unsubscribe("test_channel")
    
    async def test_service_configuration_validation(
        self,
        flow_orchestrator,
        event_gateway,
        data_validator,
        flow_monitor,
        test_service_client
    ):
        """Test service configuration validation."""
        
        # Test flow orchestrator configuration
        response = await test_service_client.http_client.get(
            f"{flow_orchestrator['endpoint']}/orchestrator/config"
        )
        response.raise_for_status()
        config = response.json()
        
        assert "flows" in config
        assert len(config["flows"]) > 0
        assert "flow_execution_enabled" in config
        
        # Test event gateway configuration
        response = await test_service_client.http_client.get(
            f"{event_gateway['endpoint']}/gateway/config"
        )
        response.raise_for_status()
        config = response.json()
        
        assert "event_routing_enabled" in config
        assert "topics" in config
        assert len(config["topics"]) > 0
        
        # Test data validator configuration
        response = await test_service_client.http_client.get(
            f"{data_validator['endpoint']}/validator/config"
        )
        response.raise_for_status()
        config = response.json()
        
        assert "validation_enabled" in config
        assert "validation_rules" in config
        assert len(config["validation_rules"]) > 0
        
        # Test flow monitor configuration
        response = await test_service_client.http_client.get(
            f"{flow_monitor['endpoint']}/monitor/config"
        )
        response.raise_for_status()
        config = response.json()
        
        assert "flow_monitoring_enabled" in config
        assert "monitored_flows" in config
        assert len(config["monitored_flows"]) > 0
    
    @pytest.mark.slow
    async def test_service_startup_order(
        self,
        service_manager,
        integration_test_config
    ):
        """Test that services can start in any order (no hard dependencies)."""
        services = integration_test_config["expected_services"]
        
        # Test reverse startup order
        reversed_services = list(reversed(services))
        service_info = {}
        
        for i, service_name in enumerate(reversed_services):
            port = 8100 + i
            service_dir = service_name
            
            try:
                info = await service_manager.start_service(
                    service_name, 
                    port, 
                    service_dir,
                    timeout=integration_test_config["service_startup_timeout"]
                )
                service_info[service_name] = info
                assert info["ready"], f"Service {service_name} failed to start in reverse order"
            finally:
                # Clean up
                await service_manager.stop_service(service_name)
    
    async def test_service_graceful_shutdown(
        self,
        service_manager,
        integration_test_config
    ):
        """Test that services shut down gracefully."""
        # Start a test service
        service_name = "flow-orchestrator"
        port = 8200
        
        service_info = await service_manager.start_service(
            service_name, port, service_name, timeout=30
        )
        
        assert service_info["ready"]
        
        # Verify it's running
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:{port}/healthz")
            assert response.status_code == 200
        
        # Stop the service
        await service_manager.stop_service(service_name)
        
        # Verify it's stopped
        await asyncio.sleep(2)  # Give time for shutdown
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"http://localhost:{port}/healthz", timeout=2.0)
                # Should not reach here if service is properly stopped
                assert False, "Service did not shut down properly"
            except httpx.ConnectError:
                # Expected - service should be unreachable
                pass


@pytest.mark.integration
@pytest.mark.redis_required
class TestServiceDependencies:
    """Test service dependency handling."""
    
    async def test_services_handle_redis_unavailable(
        self,
        service_manager,
        integration_test_config
    ):
        """Test service behavior when Redis is unavailable."""
        # Note: This test assumes Redis is running for other tests
        # In a real environment, you'd stop Redis temporarily
        
        # Start a service with invalid Redis URL
        import os
        old_redis_url = os.environ.get("REDIS_URL")
        
        try:
            os.environ["REDIS_URL"] = "redis://localhost:9999"  # Invalid Redis port
            
            service_name = "flow-orchestrator"
            port = 8201
            
            # Service should start but report unhealthy
            service_info = await service_manager.start_service(
                service_name, port, service_name, timeout=30
            )
            
            # Health check should indicate Redis issues
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://localhost:{port}/healthz")
                health = response.json()
                
                # Service might be healthy but Redis dependency should be unhealthy
                if "dependencies" in health:
                    assert health["dependencies"]["redis"]["status"] == "unhealthy"
                    
        finally:
            # Restore Redis URL
            if old_redis_url:
                os.environ["REDIS_URL"] = old_redis_url
            else:
                os.environ.pop("REDIS_URL", None)
            
            await service_manager.stop_service(service_name)
    
    async def test_service_discovery(
        self,
        flow_orchestrator,
        event_gateway,
        data_validator,
        flow_monitor,
        test_service_client
    ):
        """Test that services can discover each other."""
        services = {
            "flow-orchestrator": flow_orchestrator,
            "event-gateway": event_gateway,
            "data-validator": data_validator,
            "flow-monitor": flow_monitor
        }
        
        # Each service should know about the others through configuration
        for service_name, service_info in services.items():
            response = await test_service_client.http_client.get(
                f"{service_info['endpoint']}/healthz"
            )
            response.raise_for_status()
            
            health = response.json()
            assert health["status"] == "healthy"
            assert health["service"] == service_name