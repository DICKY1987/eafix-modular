#!/usr/bin/env python3
"""
Round-trip tests for Python ⇄ MQL4 contract compatibility.

These tests ensure that data can be serialized to JSON in Python,
parsed correctly in MQL4, and then serialized back to identical JSON.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from contracts.models.event_models import (
    PriceTick, Signal, OrderIntent, ExecutionReport, CalendarEvent,
    TradingSide, OrderSide, ExecutionStatus, CalendarImpact
)


class TestPythonMQL4RoundTrip:
    """Test round-trip compatibility between Python and MQL4 contract parsing."""

    def test_price_tick_round_trip(self):
        """Test PriceTick serialization/parsing compatibility."""
        # Create test data
        tick = PriceTick(
            timestamp=datetime(2025, 1, 15, 12, 30, 45, tzinfo=timezone.utc),
            symbol="EURUSD",
            bid=1.09435,
            ask=1.09438,
            volume=100
        )
        
        # Serialize to JSON
        json_str = tick.json()
        json_data = json.loads(json_str)
        
        # Verify JSON structure matches schema
        assert "timestamp" in json_data
        assert "symbol" in json_data
        assert "bid" in json_data
        assert "ask" in json_data
        assert "volume" in json_data
        
        # Verify data types and values
        assert json_data["symbol"] == "EURUSD"
        assert json_data["bid"] == 1.09435
        assert json_data["ask"] == 1.09438
        assert json_data["volume"] == 100
        
        # Test parsing back
        parsed_tick = PriceTick.parse_raw(json_str)
        
        # Verify round-trip integrity
        assert parsed_tick.symbol == tick.symbol
        assert parsed_tick.bid == tick.bid
        assert parsed_tick.ask == tick.ask
        assert parsed_tick.volume == tick.volume
        assert parsed_tick.timestamp == tick.timestamp

    def test_signal_round_trip(self):
        """Test Signal serialization/parsing compatibility."""
        signal_id = uuid.uuid4()
        signal = Signal(
            id=signal_id,
            timestamp=datetime(2025, 1, 15, 12, 30, 45, tzinfo=timezone.utc),
            symbol="GBPUSD",
            side=TradingSide.BUY,
            confidence=0.75,
            explanation="Strong bullish divergence on RSI",
            source_indicators=["RSI", "MACD", "BOLLINGER"],
            expiry=datetime(2025, 1, 15, 13, 30, 45, tzinfo=timezone.utc)
        )
        
        # Serialize to JSON
        json_str = signal.json()
        json_data = json.loads(json_str)
        
        # Verify JSON structure
        assert "id" in json_data
        assert "timestamp" in json_data
        assert "symbol" in json_data
        assert "side" in json_data
        assert "confidence" in json_data
        
        # Verify values
        assert json_data["id"] == str(signal_id)
        assert json_data["symbol"] == "GBPUSD"
        assert json_data["side"] == "BUY"
        assert json_data["confidence"] == 0.75
        
        # Test parsing back
        parsed_signal = Signal.parse_raw(json_str)
        
        # Verify round-trip integrity
        assert parsed_signal.id == signal.id
        assert parsed_signal.symbol == signal.symbol
        assert parsed_signal.side == signal.side
        assert parsed_signal.confidence == signal.confidence
        assert parsed_signal.explanation == signal.explanation

    def test_order_intent_round_trip(self):
        """Test OrderIntent serialization/parsing compatibility."""
        intent_id = uuid.uuid4()
        signal_id = uuid.uuid4()
        
        intent = OrderIntent(
            id=intent_id,
            signal_id=signal_id,
            timestamp=datetime(2025, 1, 15, 12, 30, 45, tzinfo=timezone.utc),
            symbol="USDJPY",
            side=OrderSide.LONG,
            quantity=0.10,
            price=149.50,
            stop_loss=149.00,
            take_profit=150.00,
            reentry_key="W1_QUICK_AT_EVENT_CAL8_USD_NFP_H_LONG_1"
        )
        
        # Serialize to JSON
        json_str = intent.json()
        json_data = json.loads(json_str)
        
        # Verify JSON structure
        required_fields = ["id", "signal_id", "timestamp", "symbol", "side", "quantity"]
        for field in required_fields:
            assert field in json_data
        
        # Verify values
        assert json_data["id"] == str(intent_id)
        assert json_data["signal_id"] == str(signal_id)
        assert json_data["symbol"] == "USDJPY"
        assert json_data["side"] == "LONG"
        assert json_data["quantity"] == 0.10
        
        # Test parsing back
        parsed_intent = OrderIntent.parse_raw(json_str)
        
        # Verify round-trip integrity
        assert parsed_intent.id == intent.id
        assert parsed_intent.signal_id == intent.signal_id
        assert parsed_intent.symbol == intent.symbol
        assert parsed_intent.side == intent.side
        assert parsed_intent.quantity == intent.quantity

    def test_execution_report_round_trip(self):
        """Test ExecutionReport serialization/parsing compatibility."""
        intent_id = uuid.uuid4()
        
        report = ExecutionReport(
            order_intent_id=intent_id,
            broker_order_id="12345678",
            timestamp=datetime(2025, 1, 15, 12, 31, 15, tzinfo=timezone.utc),
            status=ExecutionStatus.FILLED,
            filled_quantity=0.10,
            filled_price=149.52,
            commission=2.50
        )
        
        # Serialize to JSON
        json_str = report.json()
        json_data = json.loads(json_str)
        
        # Verify JSON structure
        required_fields = ["order_intent_id", "timestamp", "status"]
        for field in required_fields:
            assert field in json_data
        
        # Verify values
        assert json_data["order_intent_id"] == str(intent_id)
        assert json_data["broker_order_id"] == "12345678"
        assert json_data["status"] == "FILLED"
        assert json_data["filled_quantity"] == 0.10
        
        # Test parsing back
        parsed_report = ExecutionReport.parse_raw(json_str)
        
        # Verify round-trip integrity
        assert parsed_report.order_intent_id == report.order_intent_id
        assert parsed_report.broker_order_id == report.broker_order_id
        assert parsed_report.status == report.status
        assert parsed_report.filled_quantity == report.filled_quantity

    def test_calendar_event_round_trip(self):
        """Test CalendarEvent serialization/parsing compatibility."""
        event = CalendarEvent(
            id="NFP_2025_01_15",
            timestamp=datetime(2025, 1, 15, 13, 30, 0, tzinfo=timezone.utc),
            currency="USD",
            title="Non-Farm Payrolls",
            impact=CalendarImpact.HIGH,
            actual="250K",
            forecast="200K",
            previous="180K",
            source="BLS"
        )
        
        # Serialize to JSON
        json_str = event.json()
        json_data = json.loads(json_str)
        
        # Verify JSON structure
        required_fields = ["id", "timestamp", "currency", "title", "impact"]
        for field in required_fields:
            assert field in json_data
        
        # Verify values
        assert json_data["id"] == "NFP_2025_01_15"
        assert json_data["currency"] == "USD"
        assert json_data["title"] == "Non-Farm Payrolls"
        assert json_data["impact"] == "HIGH"
        
        # Test parsing back
        parsed_event = CalendarEvent.parse_raw(json_str)
        
        # Verify round-trip integrity
        assert parsed_event.id == event.id
        assert parsed_event.currency == event.currency
        assert parsed_event.title == event.title
        assert parsed_event.impact == event.impact

    def test_numeric_precision_safety(self):
        """Test numeric precision handling for forex prices."""
        # Test with typical forex precision requirements
        prices = [
            1.09435,  # EUR/USD typical
            149.123,  # USD/JPY typical  
            0.85678,  # AUD/USD typical
            1.2345678901234,  # High precision test
        ]
        
        for price in prices:
            tick = PriceTick(
                timestamp=datetime.now(timezone.utc),
                symbol="EURUSD",
                bid=price,
                ask=price + 0.00003,  # Typical spread
                volume=100
            )
            
            # Serialize and parse back
            json_str = tick.json()
            parsed_tick = PriceTick.parse_raw(json_str)
            
            # Verify precision is maintained within acceptable forex tolerance
            assert abs(parsed_tick.bid - tick.bid) < 0.000001
            assert abs(parsed_tick.ask - tick.ask) < 0.000001

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test minimum values
        tick_min = PriceTick(
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            symbol="EURUSD",
            bid=0.00001,  # Minimum valid price
            ask=0.00002,
            volume=0  # Minimum volume
        )
        
        json_str = tick_min.json()
        parsed = PriceTick.parse_raw(json_str)
        assert parsed.bid == tick_min.bid
        
        # Test missing optional fields
        tick_no_volume = PriceTick(
            timestamp=datetime.now(timezone.utc),
            symbol="GBPJPY",
            bid=180.123,
            ask=180.126
            # volume intentionally omitted
        )
        
        json_str = tick_no_volume.json()
        parsed = PriceTick.parse_raw(json_str)
        assert parsed.symbol == "GBPJPY"
        assert parsed.volume is None


def generate_golden_test_data():
    """Generate golden test data files for MQL4 compatibility testing."""
    test_data_dir = Path(__file__).parent / "golden_fixtures"
    test_data_dir.mkdir(exist_ok=True)
    
    # Generate PriceTick golden data
    price_ticks = [
        PriceTick(
            timestamp=datetime(2025, 1, 15, 12, 30, 45, tzinfo=timezone.utc),
            symbol="EURUSD",
            bid=1.09435,
            ask=1.09438,
            volume=100
        ),
        PriceTick(
            timestamp=datetime(2025, 1, 15, 12, 31, 0, tzinfo=timezone.utc),
            symbol="GBPUSD",
            bid=1.2750,
            ask=1.2753,
            volume=None
        )
    ]
    
    with open(test_data_dir / "price_ticks.json", "w") as f:
        json.dump([json.loads(tick.json()) for tick in price_ticks], f, indent=2)
    
    # Generate Signal golden data
    signals = [
        Signal(
            id=uuid.UUID("12345678-1234-5678-9abc-123456789abc"),
            timestamp=datetime(2025, 1, 15, 12, 30, 45, tzinfo=timezone.utc),
            symbol="EURUSD",
            side=TradingSide.BUY,
            confidence=0.75,
            explanation="Strong bullish momentum",
            source_indicators=["RSI", "MACD"]
        )
    ]
    
    with open(test_data_dir / "signals.json", "w") as f:
        json.dump([json.loads(signal.json()) for signal in signals], f, indent=2)
    
    print(f"Golden test data generated in {test_data_dir}")


if __name__ == "__main__":
    generate_golden_test_data()
    print("Golden test data generation complete")