# DOC_ID: DOC-TEST-0025
"""
Performance Monitoring Tests

Tests for flow monitor service performance analysis,
latency tracking, and system health monitoring across
the entire EAFIX pipeline.
"""

import pytest
import asyncio
import time
from typing import Dict, Any, List
from datetime import datetime, timezone


@pytest.mark.integration
@pytest.mark.services_required
@pytest.mark.redis_required
@pytest.mark.slow
class TestPerformanceMonitoring:
    """Test flow monitor performance tracking capabilities."""
    
    async def test_flow_latency_measurement(
        self,
        flow_orchestrator,
        flow_monitor,
        test_event_publisher,
        test_service_client,
        sample_price_tick
    ):
        """Test end-to-end flow latency measurement."""
        
        # Start a price-to-signal flow
        flow_response = await test_service_client.trigger_flow(
            flow_orchestrator["endpoint"],
            "price_to_signal_flow",
            {"initial_price_tick": sample_price_tick}
        )
        
        flow_execution_id = flow_response["execution_id"]
        
        # Publish price tick to trigger pipeline
        start_time = time.time()
        await test_event_publisher.publish_price_tick(sample_price_tick)
        
        # Wait for flow processing
        await asyncio.sleep(5)
        
        # Get flow traces with latency information
        traces = await test_service_client.get_flow_traces(flow_monitor["endpoint"])
        
        # Find our flow trace
        our_trace = None
        for trace in traces:
            if (trace["flow_name"] == "price_to_signal_flow" and 
                sample_price_tick["symbol"] in str(trace)):
                our_trace = trace
                break
        
        if our_trace:
            assert "total_latency_ms" in our_trace
            assert "stages" in our_trace
            
            # Verify latency measurements
            total_latency = our_trace["total_latency_ms"]
            assert total_latency > 0
            assert total_latency < 30000  # Should complete within 30 seconds
            
            # Check individual stage latencies
            for stage in our_trace["stages"]:
                if "latency_ms" in stage:
                    assert stage["latency_ms"] >= 0
                    assert stage["latency_ms"] < total_latency
    
    async def test_throughput_monitoring(
        self,
        flow_orchestrator,
        flow_monitor,
        test_event_publisher,
        test_service_client,
        price_tick_generator
    ):
        """Test throughput monitoring across multiple flows."""
        
        # Generate multiple price ticks rapidly
        events_count = 10
        price_ticks = [
            price_tick_generator(
                symbol=f"THROUGHPUT{i}",
                bid=1.1000 + (i * 0.0001),
                timestamp=f"2025-01-15T10:3{i % 10}:{i % 60:02d}Z"
            )
            for i in range(events_count)
        ]
        
        # Start multiple flows
        flow_executions = []
        start_time = time.time()
        
        for i, tick in enumerate(price_ticks):
            flow_response = await test_service_client.trigger_flow(
                flow_orchestrator["endpoint"],
                "price_to_signal_flow",
                {"initial_price_tick": tick}
            )
            flow_executions.append(flow_response["execution_id"])
            
            # Publish price tick
            await test_event_publisher.publish_price_tick(tick)
            
            # Small delay between events
            await asyncio.sleep(0.1)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Wait for flows to process
        await asyncio.sleep(8)
        
        # Get performance metrics
        response = await test_service_client.http_client.get(
            f"{flow_monitor['endpoint']}/monitor/performance/summary"
        )
        
        if response.status_code == 200:
            performance_data = response.json()
            
            assert "flows_per_second" in performance_data or "throughput" in performance_data
            assert "avg_latency_ms" in performance_data or "latency" in performance_data
            
            # Validate throughput calculations
            if "flows_per_second" in performance_data:
                throughput = performance_data["flows_per_second"]
                assert throughput > 0
                
                # Should process at reasonable rate
                expected_min_throughput = events_count / (total_time + 10)  # Allow processing time
                assert throughput >= expected_min_throughput * 0.5  # 50% tolerance
    
    async def test_latency_percentile_analysis(
        self,
        flow_monitor,
        test_service_client
    ):
        """Test latency percentile analysis."""
        
        # Get latency percentile data
        response = await test_service_client.http_client.get(
            f"{flow_monitor['endpoint']}/monitor/latency/percentiles"
        )
        
        if response.status_code == 200:
            percentiles = response.json()
            
            assert "percentiles" in percentiles
            percentile_data = percentiles["percentiles"]
            
            # Should include common percentiles
            expected_percentiles = ["p50", "p75", "p90", "p95", "p99"]
            available_percentiles = list(percentile_data.keys())
            
            common_percentiles = set(expected_percentiles) & set(available_percentiles)
            assert len(common_percentiles) >= 3  # At least 3 percentiles
            
            # Validate percentile values
            for p in common_percentiles:
                latency = percentile_data[p]
                assert latency >= 0
                assert latency < 60000  # Less than 60 seconds
    
    async def test_performance_degradation_detection(
        self,
        flow_monitor,
        test_service_client,
        flow_orchestrator,
        test_event_publisher,
        price_tick_generator
    ):
        """Test performance degradation detection."""
        
        # Get baseline performance
        baseline_response = await test_service_client.http_client.get(
            f"{flow_monitor['endpoint']}/monitor/performance/baseline"
        )
        
        # Create performance load
        for i in range(5):
            tick = price_tick_generator(
                symbol=f"PERF{i}",
                bid=1.1000 + i * 0.0001
            )
            
            # Start flow
            await test_service_client.trigger_flow(
                flow_orchestrator["endpoint"],
                "price_to_signal_flow",
                {"initial_price_tick": tick}
            )
            
            # Publish event
            await test_event_publisher.publish_price_tick(tick)
            
            # Short delay
            await asyncio.sleep(0.2)
        
        # Wait for processing
        await asyncio.sleep(5)
        
        # Check for performance alerts
        response = await test_service_client.http_client.get(
            f"{flow_monitor['endpoint']}/monitor/alerts/performance"
        )
        
        if response.status_code == 200:
            alerts = response.json()
            
            assert "alerts" in alerts
            alert_list = alerts["alerts"]
            
            # May or may not have alerts depending on system performance
            assert isinstance(alert_list, list)
            
            for alert in alert_list:
                assert "alert_type" in alert
                assert "severity" in alert
                assert "message" in alert
                assert "timestamp" in alert
    
    async def test_flow_success_rate_monitoring(
        self,
        flow_monitor,
        flow_orchestrator,
        test_service_client,
        test_event_publisher,
        price_tick_generator
    ):
        """Test flow success rate monitoring."""
        
        # Create mix of valid and potentially problematic events
        events = []
        
        # Valid events
        for i in range(5):
            events.append(price_tick_generator(
                symbol=f"VALID{i}",
                bid=1.1000 + i * 0.0001
            ))
        
        # Potentially problematic events (extreme values)
        for i in range(2):
            events.append(price_tick_generator(
                symbol=f"EXTREME{i}",
                bid=0.0001,  # Extremely low price
                ask=0.0002   # Very wide spread percentage-wise
            ))
        
        # Process all events
        flow_executions = []
        for event in events:
            flow_response = await test_service_client.trigger_flow(
                flow_orchestrator["endpoint"],
                "price_to_signal_flow",
                {"initial_price_tick": event}
            )
            flow_executions.append(flow_response["execution_id"])
            
            await test_event_publisher.publish_price_tick(event)
            await asyncio.sleep(0.1)
        
        # Wait for processing
        await asyncio.sleep(8)
        
        # Get success rate metrics
        response = await test_service_client.http_client.get(
            f"{flow_monitor['endpoint']}/monitor/success-rate"
        )
        
        if response.status_code == 200:
            success_data = response.json()
            
            assert "overall_success_rate" in success_data
            success_rate = success_data["overall_success_rate"]
            
            assert 0.0 <= success_rate <= 1.0
            
            # Should have processed some flows successfully
            assert success_rate > 0.3  # At least 30% success rate
            
            if "flow_breakdown" in success_data:
                breakdown = success_data["flow_breakdown"]
                assert "price_to_signal_flow" in breakdown
    
    async def test_real_time_monitoring_updates(
        self,
        flow_monitor,
        test_service_client,
        redis_client
    ):
        """Test real-time monitoring updates via Redis."""
        
        # Subscribe to monitoring updates
        monitoring_topic = "eafix.flow.monitoring"
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(monitoring_topic)
        
        # Get current monitoring status
        response = await test_service_client.http_client.get(
            f"{flow_monitor['endpoint']}/monitor/status/realtime"
        )
        
        if response.status_code == 200:
            status = response.json()
            
            assert "active_flows" in status
            assert "monitoring_enabled" in status
            assert status["monitoring_enabled"] == True
            
            # Check active monitoring
            active_flows = status["active_flows"]
            assert isinstance(active_flows, (list, int))
        
        await pubsub.unsubscribe(monitoring_topic)
    
    async def test_historical_performance_data(
        self,
        flow_monitor,
        test_service_client
    ):
        """Test historical performance data retrieval."""
        
        # Get historical performance data
        response = await test_service_client.http_client.get(
            f"{flow_monitor['endpoint']}/monitor/history/performance",
            params={"hours": 1}  # Last hour
        )
        
        if response.status_code == 200:
            history = response.json()
            
            assert "time_range" in history
            assert "data_points" in history
            
            data_points = history["data_points"]
            assert isinstance(data_points, list)
            
            # Validate data point structure
            for point in data_points[:5]:  # Check first 5 points
                assert "timestamp" in point
                assert "latency_ms" in point or "performance_metrics" in point
    
    async def test_flow_monitoring_configuration(
        self,
        flow_monitor,
        test_service_client
    ):
        """Test flow monitoring configuration."""
        
        # Get monitoring configuration
        response = await test_service_client.http_client.get(
            f"{flow_monitor['endpoint']}/monitor/config"
        )
        response.raise_for_status()
        config = response.json()
        
        assert "flow_monitoring_enabled" in config
        assert "monitored_flows" in config
        assert config["flow_monitoring_enabled"] == True
        
        # Validate monitored flows configuration
        monitored_flows = config["monitored_flows"]
        assert len(monitored_flows) > 0
        
        for flow_name, flow_config in monitored_flows.items():
            assert "enabled" in flow_config
            assert "total_expected_latency_ms" in flow_config
            assert "success_rate_threshold" in flow_config
            
            # Latency thresholds should be reasonable
            expected_latency = flow_config["total_expected_latency_ms"]
            assert 0 < expected_latency < 300000  # Between 0 and 5 minutes
            
            # Success rate threshold should be reasonable
            success_threshold = flow_config["success_rate_threshold"]
            assert 0.0 <= success_threshold <= 1.0


@pytest.mark.integration
@pytest.mark.services_required
@pytest.mark.slow
class TestSystemHealthMonitoring:
    """Test overall system health monitoring."""
    
    async def test_service_health_aggregation(
        self,
        flow_monitor,
        flow_orchestrator,
        event_gateway,
        data_validator,
        test_service_client
    ):
        """Test aggregated service health monitoring."""
        
        # Get system health overview
        response = await test_service_client.http_client.get(
            f"{flow_monitor['endpoint']}/monitor/system/health"
        )
        
        if response.status_code == 200:
            health = response.json()
            
            assert "overall_health" in health
            assert "services" in health
            
            overall_health = health["overall_health"]
            assert overall_health in ["healthy", "degraded", "unhealthy"]
            
            # Service health details
            services = health["services"]
            expected_services = ["flow-orchestrator", "event-gateway", "data-validator"]
            
            for service_name in expected_services:
                if service_name in services:
                    service_health = services[service_name]
                    assert "status" in service_health
                    assert "last_check" in service_health
    
    async def test_resource_monitoring(
        self,
        flow_monitor,
        test_service_client
    ):
        """Test system resource monitoring."""
        
        # Get resource utilization data
        response = await test_service_client.http_client.get(
            f"{flow_monitor['endpoint']}/monitor/system/resources"
        )
        
        if response.status_code == 200:
            resources = response.json()
            
            expected_metrics = ["cpu_percent", "memory_percent", "disk_usage"]
            available_metrics = list(resources.keys())
            
            common_metrics = set(expected_metrics) & set(available_metrics)
            assert len(common_metrics) >= 1  # At least one resource metric
            
            # Validate metric values
            for metric in common_metrics:
                value = resources[metric]
                assert 0 <= value <= 100  # Percentage values
    
    async def test_flow_health_correlation(
        self,
        flow_monitor,
        test_service_client,
        flow_orchestrator,
        test_event_publisher,
        sample_price_tick
    ):
        """Test correlation between flow performance and system health."""
        
        # Start a flow
        flow_response = await test_service_client.trigger_flow(
            flow_orchestrator["endpoint"],
            "price_to_signal_flow",
            {"initial_price_tick": sample_price_tick}
        )
        
        await test_event_publisher.publish_price_tick(sample_price_tick)
        
        # Wait for processing
        await asyncio.sleep(3)
        
        # Get flow health
        response = await test_service_client.http_client.get(
            f"{flow_monitor['endpoint']}/monitor/flows/health"
        )
        
        if response.status_code == 200:
            flow_health = response.json()
            
            assert "flows" in flow_health
            flows = flow_health["flows"]
            
            # Look for our flow
            if "price_to_signal_flow" in flows:
                flow_info = flows["price_to_signal_flow"]
                
                assert "health_score" in flow_info
                health_score = flow_info["health_score"]
                assert 0.0 <= health_score <= 1.0
                
                if "performance_indicators" in flow_info:
                    indicators = flow_info["performance_indicators"]
                    assert isinstance(indicators, dict)
    
    async def test_alert_generation(
        self,
        flow_monitor,
        test_service_client
    ):
        """Test monitoring alert generation."""
        
        # Get current alerts
        response = await test_service_client.http_client.get(
            f"{flow_monitor['endpoint']}/monitor/alerts"
        )
        
        if response.status_code == 200:
            alerts = response.json()
            
            assert "active_alerts" in alerts
            active_alerts = alerts["active_alerts"]
            assert isinstance(active_alerts, list)
            
            # Validate alert structure
            for alert in active_alerts[:3]:  # Check first 3 alerts
                assert "alert_id" in alert
                assert "severity" in alert
                assert "message" in alert
                assert "timestamp" in alert
                assert alert["severity"] in ["low", "medium", "high", "critical"]
    
    async def test_monitoring_metrics_export(
        self,
        flow_monitor,
        test_service_client
    ):
        """Test monitoring metrics export."""
        
        # Get Prometheus metrics
        metrics = await test_service_client.get_service_metrics(
            flow_monitor["endpoint"]
        )
        
        assert "service" in metrics
        assert metrics["service"] == "flow-monitor"
        
        # Flow monitoring specific metrics
        expected_metrics = [
            "flows_monitored",
            "traces_collected",
            "avg_flow_latency_ms",
            "flow_success_rate"
        ]
        
        available_metrics = list(metrics.keys())
        common_metrics = set(expected_metrics) & set(available_metrics)
        
        # Should have at least some flow monitoring metrics
        assert len(common_metrics) >= 2
        
        for metric in common_metrics:
            value = metrics[metric]
            assert isinstance(value, (int, float))
            assert value >= 0


@pytest.mark.integration
@pytest.mark.services_required
class TestMonitoringIntegration:
    """Test monitoring integration with other services."""
    
    async def test_orchestrator_monitoring_integration(
        self,
        flow_orchestrator,
        flow_monitor,
        test_service_client
    ):
        """Test integration between flow orchestrator and monitor."""
        
        # Get orchestrator flows
        response = await test_service_client.http_client.get(
            f"{flow_orchestrator['endpoint']}/orchestrator/flows"
        )
        response.raise_for_status()
        orchestrator_flows = response.json()
        
        # Get monitored flows
        response = await test_service_client.http_client.get(
            f"{flow_monitor['endpoint']}/monitor/flows"
        )
        response.raise_for_status()
        monitored_flows = response.json()
        
        # There should be overlap between orchestrator and monitored flows
        orchestrator_flow_names = set(orchestrator_flows.get("available_flows", []))
        monitored_flow_names = set(monitored_flows.get("monitored_flows", []))
        
        common_flows = orchestrator_flow_names & monitored_flow_names
        assert len(common_flows) > 0
    
    async def test_telemetry_integration(
        self,
        flow_monitor,
        telemetry_daemon,
        test_service_client
    ):
        """Test integration with telemetry daemon."""
        
        # Get flow monitor telemetry
        monitor_metrics = await test_service_client.get_service_metrics(
            flow_monitor["endpoint"]
        )
        
        # Get telemetry daemon metrics
        telemetry_metrics = await test_service_client.get_service_metrics(
            telemetry_daemon["endpoint"]
        )
        
        # Both should be operational
        assert monitor_metrics["service"] == "flow-monitor"
        assert telemetry_metrics["service"] == "telemetry-daemon"
        
        # Both should have uptime
        assert monitor_metrics["uptime_seconds"] > 0
        assert telemetry_metrics["uptime_seconds"] > 0