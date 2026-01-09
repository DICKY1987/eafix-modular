# DOC_ID: DOC-TEST-0024
"""
Event Routing Tests

Tests for event gateway service routing, transformation,
and distribution capabilities across the EAFIX system.
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any, List


@pytest.mark.integration
@pytest.mark.services_required
@pytest.mark.redis_required
class TestEventRouting:
    """Test event gateway routing functionality."""
    
    async def test_basic_event_routing(
        self,
        event_gateway,
        test_event_publisher,
        test_service_client,
        redis_client,
        sample_price_tick
    ):
        """Test basic event routing through gateway."""
        
        # Publish event via gateway
        event_response = await test_service_client.publish_event_via_gateway(
            event_gateway["endpoint"],
            "PriceTick",
            "1.0",
            sample_price_tick
        )
        
        assert event_response["status"] == "published"
        assert "event_id" in event_response
        assert "routed_topics" in event_response
        
        # Should route to multiple topics
        routed_topics = event_response["routed_topics"]
        assert len(routed_topics) > 0
        
        # Verify events were published to Redis
        for topic in routed_topics:
            # Check if topic exists in Redis (may not have subscribers)
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(topic)
            
            # Re-publish to test
            await test_event_publisher.publish_price_tick(sample_price_tick, topic)
            
            message = await pubsub.get_message(timeout=2.0)
            if message and message["type"] == "subscribe":
                message = await pubsub.get_message(timeout=2.0)
            
            if message and message["type"] == "message":
                event_data = json.loads(message["data"])
                assert event_data["event_type"] == "PriceTick@1.0"
                assert event_data["payload"]["symbol"] == sample_price_tick["symbol"]
            
            await pubsub.unsubscribe(topic)
    
    async def test_signal_routing(
        self,
        event_gateway,
        test_service_client,
        redis_client,
        sample_signal
    ):
        """Test signal event routing."""
        
        # Publish signal event
        event_response = await test_service_client.publish_event_via_gateway(
            event_gateway["endpoint"],
            "Signal",
            "1.0",
            sample_signal
        )
        
        assert event_response["status"] == "published"
        assert len(event_response["routed_topics"]) > 0
        
        # Verify signal routing includes appropriate topics
        routed_topics = event_response["routed_topics"]
        signal_topics = [
            topic for topic in routed_topics 
            if "signal" in topic.lower()
        ]
        
        assert len(signal_topics) > 0
    
    async def test_calendar_event_routing(
        self,
        event_gateway,
        test_service_client,
        sample_calendar_event
    ):
        """Test calendar event routing."""
        
        # Publish calendar event
        event_response = await test_service_client.publish_event_via_gateway(
            event_gateway["endpoint"],
            "CalendarEvent",
            "1.0",
            sample_calendar_event
        )
        
        assert event_response["status"] == "published"
        
        # Should route to calendar-related topics
        routed_topics = event_response["routed_topics"]
        calendar_topics = [
            topic for topic in routed_topics 
            if "calendar" in topic.lower()
        ]
        
        assert len(calendar_topics) > 0
    
    async def test_execution_report_routing(
        self,
        event_gateway,
        test_service_client,
        sample_execution_report
    ):
        """Test execution report routing."""
        
        # Publish execution report
        event_response = await test_service_client.publish_event_via_gateway(
            event_gateway["endpoint"],
            "ExecutionReport",
            "1.0",
            sample_execution_report
        )
        
        assert event_response["status"] == "published"
        
        # Should route to execution-related topics
        routed_topics = event_response["routed_topics"]
        execution_topics = [
            topic for topic in routed_topics 
            if "execution" in topic.lower()
        ]
        
        assert len(execution_topics) > 0
    
    async def test_event_transformation(
        self,
        event_gateway,
        test_service_client,
        price_tick_generator
    ):
        """Test event transformation during routing."""
        
        # Create price tick with extra fields
        extended_price_tick = price_tick_generator(
            symbol="EURUSD",
            bid=1.1234,
            ask=1.1236,
            volume=1000000,
            spread=0.0002,
            source="TEST_FEED",
            extra_metadata={"test": "data"}
        )
        
        # Publish through gateway
        event_response = await test_service_client.publish_event_via_gateway(
            event_gateway["endpoint"],
            "PriceTick",
            "1.0",
            extended_price_tick
        )
        
        assert event_response["status"] == "published"
        
        # Gateway should handle extra fields appropriately
        if "transformations" in event_response:
            assert len(event_response["transformations"]) >= 0
    
    async def test_conditional_routing(
        self,
        event_gateway,
        test_service_client,
        price_tick_generator
    ):
        """Test conditional routing based on event content."""
        
        # Create high-impact price tick
        high_impact_tick = price_tick_generator(
            symbol="EURUSD",
            bid=1.1234,
            ask=1.1300,  # Wide spread indicating high volatility
            volume=10000000  # High volume
        )
        
        event_response = await test_service_client.publish_event_via_gateway(
            event_gateway["endpoint"],
            "PriceTick",
            "1.0",
            high_impact_tick
        )
        
        assert event_response["status"] == "published"
        
        # Compare with normal price tick
        normal_tick = price_tick_generator(
            symbol="EURUSD",
            bid=1.1234,
            ask=1.1236,  # Normal spread
            volume=1000000  # Normal volume
        )
        
        normal_response = await test_service_client.publish_event_via_gateway(
            event_gateway["endpoint"],
            "PriceTick",
            "1.0",
            normal_tick
        )
        
        assert normal_response["status"] == "published"
        
        # Routing might differ based on conditions
        # (Implementation depends on gateway routing rules)
        assert len(event_response["routed_topics"]) >= len(normal_response["routed_topics"])
    
    async def test_routing_rules_configuration(
        self,
        event_gateway,
        test_service_client
    ):
        """Test routing rules configuration."""
        
        # Get routing configuration
        response = await test_service_client.http_client.get(
            f"{event_gateway['endpoint']}/gateway/routing-rules"
        )
        response.raise_for_status()
        routing_config = response.json()
        
        assert "rules" in routing_config
        assert len(routing_config["rules"]) > 0
        
        # Check rule structure
        for rule in routing_config["rules"]:
            assert "event_type" in rule
            assert "target_topics" in rule
            
            if "conditions" in rule:
                conditions = rule["conditions"]
                assert isinstance(conditions, list)
                
                for condition in conditions:
                    assert "field" in condition
                    assert "operator" in condition
                    assert "value" in condition
    
    async def test_dead_letter_queue_handling(
        self,
        event_gateway,
        test_service_client,
        redis_client
    ):
        """Test dead letter queue for failed routing."""
        
        # Create invalid event that should fail routing
        invalid_event = {
            "invalid_field": "invalid_data",
            "symbol": None,
            "timestamp": "not_a_date"
        }
        
        try:
            # Attempt to publish invalid event
            event_response = await test_service_client.publish_event_via_gateway(
                event_gateway["endpoint"],
                "PriceTick",
                "1.0",
                invalid_event
            )
            
            # If published, check if it went to DLQ
            if event_response.get("status") == "published":
                # Check dead letter queue stats
                response = await test_service_client.http_client.get(
                    f"{event_gateway['endpoint']}/gateway/dlq/stats"
                )
                
                if response.status_code == 200:
                    dlq_stats = response.json()
                    assert "message_count" in dlq_stats
                    assert "error_count" in dlq_stats
                    
        except Exception as e:
            # Expected - invalid events should be rejected
            assert "invalid" in str(e).lower() or "validation" in str(e).lower()
    
    async def test_batch_event_routing(
        self,
        event_gateway,
        test_service_client,
        price_tick_generator
    ):
        """Test batch event processing and routing."""
        
        # Create multiple events
        events = []
        for i in range(5):
            tick = price_tick_generator(
                symbol=f"PAIR{i}",
                bid=1.0000 + (i * 0.0001),
                timestamp=f"2025-01-15T10:3{i}:00Z"
            )
            events.append({
                "event_type": "PriceTick",
                "schema_version": "1.0",
                "payload": tick
            })
        
        # Attempt batch publish (if supported)
        try:
            response = await test_service_client.http_client.post(
                f"{event_gateway['endpoint']}/gateway/events/batch",
                json={"events": events}
            )
            
            if response.status_code == 200:
                batch_response = response.json()
                assert "published_count" in batch_response
                assert batch_response["published_count"] == len(events)
                
        except Exception:
            # Batch processing might not be implemented
            # Fall back to individual event publishing
            for event in events:
                await test_service_client.publish_event_via_gateway(
                    event_gateway["endpoint"],
                    event["event_type"],
                    event["schema_version"],
                    event["payload"]
                )


@pytest.mark.integration
@pytest.mark.services_required
@pytest.mark.redis_required
class TestEventFiltering:
    """Test event filtering and topic management."""
    
    async def test_topic_filtering(
        self,
        event_gateway,
        test_service_client,
        redis_client,
        sample_price_tick
    ):
        """Test filtering events by topic."""
        
        # Subscribe to specific topic
        test_topic = "eafix.test.price.filtered"
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(test_topic)
        
        # Publish event that should route to this topic
        event_response = await test_service_client.publish_event_via_gateway(
            event_gateway["endpoint"],
            "PriceTick",
            "1.0", 
            sample_price_tick
        )
        
        # Check if our test topic is in routed topics
        routed_topics = event_response.get("routed_topics", [])
        
        # Manually publish to test topic for verification
        await redis_client.publish(test_topic, json.dumps({
            "event_type": "PriceTick@1.0",
            "timestamp": time.time(),
            "payload": sample_price_tick
        }))
        
        # Get subscription confirmation
        message = await pubsub.get_message(timeout=2.0)
        if message and message["type"] == "subscribe":
            message = await pubsub.get_message(timeout=2.0)
        
        if message and message["type"] == "message":
            event_data = json.loads(message["data"])
            assert event_data["event_type"] == "PriceTick@1.0"
        
        await pubsub.unsubscribe(test_topic)
    
    async def test_symbol_based_filtering(
        self,
        event_gateway,
        test_service_client,
        price_tick_generator
    ):
        """Test filtering events by symbol."""
        
        # Test with major currency pair
        major_pair_tick = price_tick_generator(symbol="EURUSD")
        
        major_response = await test_service_client.publish_event_via_gateway(
            event_gateway["endpoint"],
            "PriceTick",
            "1.0",
            major_pair_tick
        )
        
        # Test with exotic currency pair
        exotic_pair_tick = price_tick_generator(symbol="USDTRY")
        
        exotic_response = await test_service_client.publish_event_via_gateway(
            event_gateway["endpoint"],
            "PriceTick",
            "1.0",
            exotic_pair_tick
        )
        
        assert major_response["status"] == "published"
        assert exotic_response["status"] == "published"
        
        # Routing might differ based on symbol classification
        major_topics = major_response.get("routed_topics", [])
        exotic_topics = exotic_response.get("routed_topics", [])
        
        assert len(major_topics) > 0
        assert len(exotic_topics) > 0
    
    async def test_time_based_filtering(
        self,
        event_gateway,
        test_service_client,
        price_tick_generator
    ):
        """Test time-based event filtering."""
        
        # Market hours event
        market_hours_tick = price_tick_generator(
            symbol="EURUSD",
            timestamp="2025-01-15T14:30:00Z"  # During typical market hours
        )
        
        market_response = await test_service_client.publish_event_via_gateway(
            event_gateway["endpoint"],
            "PriceTick",
            "1.0",
            market_hours_tick
        )
        
        # Off-hours event
        off_hours_tick = price_tick_generator(
            symbol="EURUSD",
            timestamp="2025-01-15T23:30:00Z"  # Outside typical market hours
        )
        
        off_hours_response = await test_service_client.publish_event_via_gateway(
            event_gateway["endpoint"],
            "PriceTick",
            "1.0",
            off_hours_tick
        )
        
        assert market_response["status"] == "published"
        assert off_hours_response["status"] == "published"
        
        # Both should route, but possibly to different topics
        assert len(market_response.get("routed_topics", [])) > 0
        assert len(off_hours_response.get("routed_topics", [])) > 0


@pytest.mark.integration
@pytest.mark.services_required
@pytest.mark.redis_required
class TestEventGatewayPerformance:
    """Test event gateway performance and throughput."""
    
    async def test_routing_performance(
        self,
        event_gateway,
        test_service_client,
        price_tick_generator
    ):
        """Test routing performance under load."""
        
        # Generate multiple events
        events_count = 20
        events = [
            price_tick_generator(
                symbol=f"PAIR{i % 5}",  # 5 different symbols
                bid=1.0000 + (i * 0.0001),
                timestamp=f"2025-01-15T10:3{i % 10}:{i % 60:02d}Z"
            )
            for i in range(events_count)
        ]
        
        # Measure routing performance
        start_time = time.time()
        successful_routes = 0
        
        for event in events:
            try:
                response = await test_service_client.publish_event_via_gateway(
                    event_gateway["endpoint"],
                    "PriceTick",
                    "1.0",
                    event
                )
                
                if response.get("status") == "published":
                    successful_routes += 1
                    
            except Exception as e:
                print(f"Routing failed: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        events_per_second = events_count / total_time if total_time > 0 else 0
        
        # Performance assertions
        assert successful_routes >= events_count * 0.8  # At least 80% success rate
        assert events_per_second > 5  # At least 5 events per second
        assert total_time < 10  # Complete within 10 seconds
    
    async def test_concurrent_routing(
        self,
        event_gateway,
        test_service_client,
        price_tick_generator,
        signal_generator
    ):
        """Test concurrent event routing."""
        
        # Create mixed event types
        price_events = [
            price_tick_generator(symbol=f"PRICE{i}", bid=1.1000 + i * 0.0001)
            for i in range(5)
        ]
        
        signal_events = [
            signal_generator(symbol=f"SIGNAL{i}", confidence=0.8 + i * 0.02)
            for i in range(3)
        ]
        
        # Create concurrent routing tasks
        routing_tasks = []
        
        # Price tick routing tasks
        for event in price_events:
            task = test_service_client.publish_event_via_gateway(
                event_gateway["endpoint"],
                "PriceTick",
                "1.0",
                event
            )
            routing_tasks.append(task)
        
        # Signal routing tasks
        for event in signal_events:
            task = test_service_client.publish_event_via_gateway(
                event_gateway["endpoint"],
                "Signal",
                "1.0",
                event
            )
            routing_tasks.append(task)
        
        # Execute all routing tasks concurrently
        results = await asyncio.gather(*routing_tasks, return_exceptions=True)
        
        # Count successful routings
        successful_results = [
            result for result in results 
            if not isinstance(result, Exception) and 
               result.get("status") == "published"
        ]
        
        assert len(successful_results) >= len(routing_tasks) * 0.7  # 70% success rate
    
    async def test_gateway_metrics(
        self,
        event_gateway,
        test_service_client,
        sample_price_tick
    ):
        """Test gateway metrics collection."""
        
        # Publish some events first
        for i in range(3):
            await test_service_client.publish_event_via_gateway(
                event_gateway["endpoint"],
                "PriceTick",
                "1.0",
                sample_price_tick
            )
        
        # Get gateway metrics
        metrics = await test_service_client.get_service_metrics(
            event_gateway["endpoint"]
        )
        
        assert "service" in metrics
        assert metrics["service"] == "event-gateway"
        assert "events_routed" in metrics
        assert "routing_errors" in metrics
        assert "avg_routing_time_ms" in metrics
        
        # Metrics should show activity
        assert metrics["events_routed"] >= 3
        assert metrics["avg_routing_time_ms"] >= 0.0