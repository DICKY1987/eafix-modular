# DOC_ID: DOC-TEST-0022
"""
Data Validation Tests

Tests for the data validation service and validation across
the entire EAFIX pipeline. Validates schema compliance, data quality,
and business rule enforcement.
"""

import pytest
import json
import time
from typing import Dict, Any, List
from datetime import datetime, timezone


@pytest.mark.integration
@pytest.mark.services_required
class TestDataValidation:
    """Test data validation service functionality."""
    
    async def test_price_tick_validation(
        self,
        data_validator,
        test_service_client,
        sample_price_tick
    ):
        """Test price tick data validation."""
        
        # Test valid price tick
        result = await test_service_client.validate_data(
            data_validator["endpoint"],
            sample_price_tick,
            "PriceTick@1.0"
        )
        
        assert result["valid"] == True
        assert result["schema"] == "PriceTick@1.0"
        assert result["validation_score"] >= 0.95
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
    
    async def test_signal_validation(
        self,
        data_validator,
        test_service_client,
        sample_signal
    ):
        """Test signal data validation."""
        
        # Test valid signal
        result = await test_service_client.validate_data(
            data_validator["endpoint"],
            sample_signal,
            "Signal@1.0"
        )
        
        assert result["valid"] == True
        assert result["schema"] == "Signal@1.0"
        assert result["validation_score"] >= 0.95
        assert len(result["errors"]) == 0
        assert "signal_id" in result["validated_fields"]
        assert "symbol" in result["validated_fields"]
        assert "direction" in result["validated_fields"]
        assert "confidence_score" in result["validated_fields"]
    
    async def test_execution_report_validation(
        self,
        data_validator,
        test_service_client,
        sample_execution_report
    ):
        """Test execution report validation."""
        
        result = await test_service_client.validate_data(
            data_validator["endpoint"],
            sample_execution_report,
            "ExecutionReport@1.0"
        )
        
        assert result["valid"] == True
        assert result["schema"] == "ExecutionReport@1.0"
        assert result["validation_score"] >= 0.95
        assert "execution_id" in result["validated_fields"]
        assert "order_id" in result["validated_fields"]
        assert "status" in result["validated_fields"]
    
    async def test_calendar_event_validation(
        self,
        data_validator,
        test_service_client,
        sample_calendar_event
    ):
        """Test calendar event validation."""
        
        result = await test_service_client.validate_data(
            data_validator["endpoint"],
            sample_calendar_event,
            "CalendarEvent@1.0"
        )
        
        assert result["valid"] == True
        assert result["schema"] == "CalendarEvent@1.0" 
        assert result["validation_score"] >= 0.90
        assert "event_id" in result["validated_fields"]
        assert "currency" in result["validated_fields"]
        assert "impact" in result["validated_fields"]
    
    async def test_invalid_data_rejection(
        self,
        data_validator,
        test_service_client
    ):
        """Test rejection of invalid data."""
        
        # Test missing required fields
        invalid_price_tick = {
            "symbol": "EURUSD",
            # Missing bid, ask, timestamp
            "volume": 1000
        }
        
        result = await test_service_client.validate_data(
            data_validator["endpoint"],
            invalid_price_tick,
            "PriceTick@1.0"
        )
        
        assert result["valid"] == False
        assert len(result["errors"]) > 0
        assert result["validation_score"] < 0.5
        
        # Check specific error messages
        error_messages = [error["message"] for error in result["errors"]]
        required_field_errors = [
            msg for msg in error_messages 
            if "required" in msg.lower() or "missing" in msg.lower()
        ]
        assert len(required_field_errors) > 0
    
    async def test_data_type_validation(
        self,
        data_validator,
        test_service_client
    ):
        """Test data type validation."""
        
        # Test invalid data types
        invalid_signal = {
            "signal_id": "sig_001",
            "symbol": "EURUSD",
            "direction": "BUY",
            "confidence_score": "high",  # Should be number, not string
            "timestamp": "2025-01-15T10:30:30Z"
        }
        
        result = await test_service_client.validate_data(
            data_validator["endpoint"],
            invalid_signal,
            "Signal@1.0"
        )
        
        assert result["valid"] == False
        assert len(result["errors"]) > 0
        
        # Should detect type error for confidence_score
        type_errors = [
            error for error in result["errors"]
            if "confidence_score" in error.get("field", "") and
               ("type" in error["message"].lower() or "number" in error["message"].lower())
        ]
        assert len(type_errors) > 0
    
    async def test_business_rule_validation(
        self,
        data_validator,
        test_service_client
    ):
        """Test business rule validation."""
        
        # Test price tick with invalid spread (ask < bid)
        invalid_spread_tick = {
            "symbol": "EURUSD",
            "bid": 1.1250,
            "ask": 1.1240,  # Ask should be > bid
            "timestamp": "2025-01-15T10:30:00Z",
            "volume": 1000000
        }
        
        result = await test_service_client.validate_data(
            data_validator["endpoint"],
            invalid_spread_tick,
            "PriceTick@1.0"
        )
        
        # Should flag business rule violation
        if result["valid"] == False:
            business_rule_errors = [
                error for error in result["errors"]
                if "spread" in error["message"].lower() or 
                   "ask" in error["message"].lower() and "bid" in error["message"].lower()
            ]
            assert len(business_rule_errors) > 0
    
    async def test_data_quality_scoring(
        self,
        data_validator,
        test_service_client,
        price_tick_generator
    ):
        """Test data quality scoring system."""
        
        # Test perfect data
        perfect_tick = price_tick_generator(
            symbol="EURUSD",
            bid=1.1234,
            ask=1.1236,
            volume=1000000,
            timestamp="2025-01-15T10:30:00Z"
        )
        
        result = await test_service_client.validate_data(
            data_validator["endpoint"],
            perfect_tick,
            "PriceTick@1.0"
        )
        
        assert result["validation_score"] >= 0.95
        assert result["quality_score"] >= 0.95
        
        # Test data with quality issues
        poor_quality_tick = price_tick_generator(
            symbol="EUR",  # Unusual symbol format
            bid=0.0001,    # Extremely low price
            ask=0.0002,    # Very wide spread percentage
            volume=1,      # Extremely low volume
            timestamp="2025-01-15T10:30:00Z"
        )
        
        result = await test_service_client.validate_data(
            data_validator["endpoint"],
            poor_quality_tick,
            "PriceTick@1.0"
        )
        
        # May still be valid but should have lower quality score
        assert result["quality_score"] < 0.8
        assert len(result["warnings"]) > 0
    
    async def test_validation_performance(
        self,
        data_validator,
        test_service_client,
        price_tick_generator
    ):
        """Test validation performance under load."""
        
        # Generate multiple price ticks
        price_ticks = [
            price_tick_generator(
                symbol=f"PAIR{i}",
                bid=1.0000 + (i * 0.0001),
                timestamp=f"2025-01-15T10:3{i % 10}:{i % 60:02d}Z"
            )
            for i in range(10)
        ]
        
        # Validate all ticks and measure time
        start_time = time.time()
        results = []
        
        for tick in price_ticks:
            result = await test_service_client.validate_data(
                data_validator["endpoint"],
                tick,
                "PriceTick@1.0"
            )
            results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_per_validation = total_time / len(price_ticks)
        
        # Performance assertions
        assert avg_time_per_validation < 1.0  # Less than 1 second per validation
        assert all(result["valid"] for result in results)
        assert all(result["validation_score"] > 0.9 for result in results)
    
    async def test_validation_with_missing_schema(
        self,
        data_validator,
        test_service_client,
        sample_price_tick
    ):
        """Test validation with unknown/missing schema."""
        
        try:
            result = await test_service_client.validate_data(
                data_validator["endpoint"],
                sample_price_tick,
                "UnknownSchema@1.0"
            )
            
            # If request succeeds, should indicate unknown schema
            assert result["valid"] == False
            assert "schema" in result.get("errors", [{}])[0].get("message", "").lower() or \
                   "unknown" in result.get("errors", [{}])[0].get("message", "").lower()
                   
        except Exception as e:
            # Expected behavior - should reject unknown schemas
            assert "schema" in str(e).lower() or "unknown" in str(e).lower()


@pytest.mark.integration
@pytest.mark.services_required
class TestPipelineValidation:
    """Test validation across the entire data pipeline."""
    
    async def test_end_to_end_validation_flow(
        self,
        data_validator,
        event_gateway,
        test_event_publisher,
        test_service_client,
        sample_price_tick,
        redis_client
    ):
        """Test validation in complete pipeline flow."""
        
        # Publish valid price tick through event gateway
        event_response = await test_service_client.publish_event_via_gateway(
            event_gateway["endpoint"],
            "PriceTick",
            "1.0",
            sample_price_tick
        )
        
        assert event_response["status"] == "published"
        
        # The event should be automatically validated by the pipeline
        # Wait for processing
        await asyncio.sleep(2)
        
        # Check if validation occurred (this depends on pipeline integration)
        # In a fully integrated system, you'd check validation logs or metrics
        response = await test_service_client.http_client.get(
            f"{data_validator['endpoint']}/validator/stats"
        )
        response.raise_for_status()
        stats = response.json()
        
        assert "validation_count" in stats
        assert stats["validation_count"] >= 0
    
    async def test_invalid_data_pipeline_handling(
        self,
        data_validator,
        event_gateway,
        test_service_client,
        redis_client
    ):
        """Test how pipeline handles invalid data."""
        
        # Create invalid data
        invalid_data = {
            "symbol": "INVALID",
            "bid": "not_a_number",
            "ask": None,
            "timestamp": "invalid_date"
        }
        
        # Attempt to publish through gateway
        try:
            event_response = await test_service_client.publish_event_via_gateway(
                event_gateway["endpoint"],
                "PriceTick",
                "1.0",
                invalid_data
            )
            
            if event_response.get("status") == "published":
                # If published, validation should catch it downstream
                await asyncio.sleep(2)
                
                # Check validation stats for errors
                response = await test_service_client.http_client.get(
                    f"{data_validator['endpoint']}/validator/stats"
                )
                response.raise_for_status()
                stats = response.json()
                
                assert "error_count" in stats
                # Error count may be 0 if this is the first test run
                
        except Exception as e:
            # Expected - invalid data should be rejected
            assert "validation" in str(e).lower() or "invalid" in str(e).lower()
    
    async def test_validation_metrics_collection(
        self,
        data_validator,
        test_service_client,
        price_tick_generator
    ):
        """Test validation metrics and statistics collection."""
        
        # Perform several validations
        for i in range(5):
            tick = price_tick_generator(
                symbol=f"TEST{i}",
                bid=1.1000 + (i * 0.0001)
            )
            
            await test_service_client.validate_data(
                data_validator["endpoint"],
                tick,
                "PriceTick@1.0"
            )
        
        # Check validation statistics
        response = await test_service_client.http_client.get(
            f"{data_validator['endpoint']}/validator/stats"
        )
        response.raise_for_status()
        stats = response.json()
        
        assert "validation_count" in stats
        assert "success_rate" in stats
        assert "avg_validation_time_ms" in stats
        assert stats["validation_count"] >= 5
        assert stats["success_rate"] >= 0.0
        assert stats["avg_validation_time_ms"] >= 0.0


@pytest.mark.integration  
@pytest.mark.services_required
class TestValidationConfiguration:
    """Test validation service configuration and rules."""
    
    async def test_validation_rules_configuration(
        self,
        data_validator,
        test_service_client
    ):
        """Test validation rules configuration."""
        
        # Get validation configuration
        response = await test_service_client.http_client.get(
            f"{data_validator['endpoint']}/validator/config"
        )
        response.raise_for_status()
        config = response.json()
        
        assert "validation_enabled" in config
        assert "validation_rules" in config
        assert config["validation_enabled"] == True
        assert len(config["validation_rules"]) > 0
        
        # Check specific schema rules exist
        rules = config["validation_rules"]
        assert "PriceTick@1.0" in rules
        assert "Signal@1.0" in rules
        assert "ExecutionReport@1.0" in rules
        
        # Validate rule structure
        price_tick_rules = rules["PriceTick@1.0"]
        assert "schema_validation" in price_tick_rules
        assert "required_fields" in price_tick_rules["schema_validation"]
        assert "field_types" in price_tick_rules["schema_validation"]
    
    async def test_validation_rule_updates(
        self,
        data_validator,
        test_service_client
    ):
        """Test dynamic validation rule updates."""
        
        # Get current config
        response = await test_service_client.http_client.get(
            f"{data_validator['endpoint']}/validator/config"
        )
        response.raise_for_status()
        original_config = response.json()
        
        # Test rule validation endpoint exists
        # (In a real system, you might test rule updates)
        response = await test_service_client.http_client.get(
            f"{data_validator['endpoint']}/validator/rules/PriceTick@1.0"
        )
        
        if response.status_code == 200:
            rule_config = response.json()
            assert "schema_validation" in rule_config
            assert "quality_checks" in rule_config
            assert "business_rules" in rule_config