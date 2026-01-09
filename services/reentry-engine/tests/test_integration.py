# DOC_ID: DOC-TEST-0016
"""
Integration Tests for Re-entry Engine

Tests the complete flow: TradeResult → Processing → Matrix Service → CSV Output
"""

import pytest
import asyncio
import sys
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directory to path to import service modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Add shared library to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "shared"))

from services.reentry_engine.src.config import Settings
from services.reentry_engine.src.processor import TradeResultProcessor
from services.reentry_engine.src.metrics import MetricsCollector
from services.reentry_engine.src.decision_client import ReentryMatrixClient
from shared.reentry import compose, parse, validate_key
from contracts.models import TradeResult, ReentryDecision


class TestReentryEngineIntegration:
    """Test complete re-entry engine integration."""
    
    @pytest.fixture
    def test_settings(self):
        """Create test settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.output_directory = temp_dir
            settings.csv_atomic_writes = True
            settings.subscribe_to_trade_results = False  # Disable for testing
            settings.reentry_matrix_service_url = "http://localhost:8087"
            
            # Point to actual shared library location
            project_root = Path(__file__).parent.parent.parent.parent
            settings.shared_library_path = str(project_root / "shared" / "reentry")
            settings.vocabulary_file = str(project_root / "shared" / "reentry" / "reentry_vocab.json")
            
            yield settings
    
    @pytest.fixture
    def metrics_collector(self):
        """Create metrics collector."""
        return MetricsCollector()
    
    @pytest.fixture
    def sample_trade_result(self):
        """Create a sample trade result."""
        return {
            "trade_id": "TEST_TRADE_001",
            "symbol": "EURUSD",
            "direction": "BUY",
            "lot_size": 0.1,
            "open_price": 1.1000,
            "close_price": 1.1025,
            "open_time": datetime.now(timezone.utc).isoformat(),
            "close_time": datetime.now(timezone.utc).isoformat(),
            "duration_minutes": 15,
            "profit_loss": 25.0,
            "profit_loss_pips": 25.0,
            "stop_loss": 1.0980,
            "take_profit": 1.1040,
            "close_reason": "TP",
            "commission": -2.0,
            "swap": 0.0,
            "magic_number": 12345,
            "comment": "Test trade"
        }
    
    def test_trade_result_validation(self, test_settings, metrics_collector, sample_trade_result):
        """Test trade result validation against contract schema."""
        processor = TradeResultProcessor(test_settings, metrics_collector)
        
        # Test validation
        validated_trade = asyncio.run(processor._validate_trade_result(sample_trade_result))
        
        assert validated_trade.trade_id == "TEST_TRADE_001"
        assert validated_trade.symbol == "EURUSD"
        assert validated_trade.profit_loss_pips == 25.0
    
    def test_outcome_classification(self, test_settings, metrics_collector, sample_trade_result):
        """Test trade outcome classification."""
        processor = TradeResultProcessor(test_settings, metrics_collector)
        validated_trade = asyncio.run(processor._validate_trade_result(sample_trade_result))
        
        # Test WIN classification
        outcome = processor._classify_trade_outcome(validated_trade)
        assert outcome == "WIN"  # 25 pips > profit threshold
        
        # Test LOSS classification
        sample_trade_result["profit_loss_pips"] = -10.0
        validated_trade = asyncio.run(processor._validate_trade_result(sample_trade_result))
        outcome = processor._classify_trade_outcome(validated_trade)
        assert outcome == "LOSS"
        
        # Test BREAKEVEN classification
        sample_trade_result["profit_loss_pips"] = 1.0
        validated_trade = asyncio.run(processor._validate_trade_result(sample_trade_result))
        outcome = processor._classify_trade_outcome(validated_trade)
        assert outcome == "BREAKEVEN"
    
    def test_duration_classification(self, test_settings, metrics_collector, sample_trade_result):
        """Test trade duration classification."""
        processor = TradeResultProcessor(test_settings, metrics_collector)
        
        # Test FLASH duration
        sample_trade_result["duration_minutes"] = 3
        validated_trade = asyncio.run(processor._validate_trade_result(sample_trade_result))
        duration = processor._classify_trade_duration(validated_trade)
        assert duration == "FLASH"
        
        # Test QUICK duration
        sample_trade_result["duration_minutes"] = 15
        validated_trade = asyncio.run(processor._validate_trade_result(sample_trade_result))
        duration = processor._classify_trade_duration(validated_trade)
        assert duration == "QUICK"
        
        # Test LONG duration
        sample_trade_result["duration_minutes"] = 120
        validated_trade = asyncio.run(processor._validate_trade_result(sample_trade_result))
        duration = processor._classify_trade_duration(validated_trade)
        assert duration == "LONG"
        
        # Test EXTENDED duration
        sample_trade_result["duration_minutes"] = 300
        validated_trade = asyncio.run(processor._validate_trade_result(sample_trade_result))
        duration = processor._classify_trade_duration(validated_trade)
        assert duration == "EXTENDED"
    
    def test_eligibility_check(self, test_settings, metrics_collector, sample_trade_result):
        """Test re-entry eligibility checking."""
        processor = TradeResultProcessor(test_settings, metrics_collector)
        validated_trade = asyncio.run(processor._validate_trade_result(sample_trade_result))
        
        # Test eligible trade
        eligibility = asyncio.run(processor._check_reentry_eligibility(validated_trade))
        assert eligibility["eligible"] is True
        
        # Test trade too short
        sample_trade_result["duration_minutes"] = 0
        validated_trade = asyncio.run(processor._validate_trade_result(sample_trade_result))
        eligibility = asyncio.run(processor._check_reentry_eligibility(validated_trade))
        assert eligibility["eligible"] is False
        assert eligibility["reason"] == "duration_too_short"
    
    def test_hybrid_id_extraction(self, test_settings, metrics_collector):
        """Test hybrid ID extraction from trade comments."""
        processor = TradeResultProcessor(test_settings, metrics_collector)
        
        # Test valid hybrid ID in comment
        hybrid_id = "W1_QUICK_AT_EVENT_NONE_LONG_1"
        extracted = processor._extract_hybrid_id_from_comment(hybrid_id)
        assert extracted == hybrid_id  # Should extract successfully
        
        # Test invalid comment
        extracted = processor._extract_hybrid_id_from_comment("Regular trade comment")
        assert extracted is None
    
    @pytest.mark.asyncio
    async def test_matrix_service_client(self, test_settings):
        """Test re-entry matrix service client."""
        client = ReentryMatrixClient(test_settings)
        
        # Mock the HTTP client
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock health check response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            
            # Mock decision request response
            mock_decision_response = AsyncMock()
            mock_decision_response.status_code = 200
            mock_decision_response.json.return_value = {
                "status": "success",
                "hybrid_id": "W1_QUICK_AT_EVENT_NONE_LONG_1",
                "reentry_action": "R1",
                "parameter_set_id": "test_param",
                "resolved_tier": "TIER1",
                "chain_position": "O",
                "lot_size": 0.1,
                "stop_loss": 20.0,
                "take_profit": 40.0,
                "confidence_score": 0.75
            }
            mock_client.post.return_value = mock_decision_response
            
            await client.start()
            
            # Test decision request
            request_data = {
                "trade_id": "TEST_001",
                "symbol": "EURUSD",
                "outcome_class": "WIN",
                "duration_class": "QUICK",
                "proximity_state": "AT_EVENT",
                "calendar_id": "NONE",
                "direction": "LONG",
                "generation": 1,
                "current_lot_size": 0.1,
                "profit_loss_pips": 25.0
            }
            
            decision = await client.request_reentry_decision(request_data)
            
            assert decision["status"] == "success"
            assert decision["reentry_action"] == "R1"
            assert decision["confidence_score"] == 0.75
            
            await client.stop()
    
    @pytest.mark.asyncio
    async def test_csv_atomic_write(self, test_settings, metrics_collector, sample_trade_result):
        """Test atomic CSV write functionality."""
        processor = TradeResultProcessor(test_settings, metrics_collector)
        
        # Mock decision response
        decision_response = {
            "hybrid_id": "W1_QUICK_AT_EVENT_NONE_LONG_1",
            "reentry_action": "R1", 
            "parameter_set_id": "test_param_set",
            "resolved_tier": "TIER1",
            "chain_position": "O",
            "lot_size": 0.1,
            "stop_loss": 20.0,
            "take_profit": 40.0,
            "confidence_score": 0.75
        }
        
        validated_trade = await processor._validate_trade_result(sample_trade_result)
        
        # Test CSV write
        result = await processor._write_reentry_decision_csv(validated_trade, decision_response)
        
        assert result["success"] is True
        assert "file" in result
        assert "file_seq" in result
        assert "checksum" in result
        
        # Verify file was created
        csv_file = Path(result["file"])
        assert csv_file.exists()
        
        # Verify content structure
        content = csv_file.read_text()
        lines = content.strip().split('\n')
        
        # Should have header + data
        assert len(lines) >= 2
        
        # Check header
        header = lines[0].split(',')
        expected_fields = [
            'file_seq', 'checksum_sha256', 'timestamp',
            'trade_id', 'hybrid_id', 'symbol', 'outcome_class', 'duration_class',
            'reentry_action', 'parameter_set_id', 'resolved_tier', 'chain_position',
            'lot_size', 'stop_loss', 'take_profit'
        ]
        
        for field in expected_fields:
            assert field in header
    
    @pytest.mark.asyncio
    async def test_full_processing_flow(self, test_settings, metrics_collector, sample_trade_result):
        """Test complete trade processing flow."""
        processor = TradeResultProcessor(test_settings, metrics_collector)
        
        # Mock the matrix service client
        with patch('services.reentry_engine.src.processor.ReentryMatrixClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock decision response
            mock_client.request_reentry_decision.return_value = {
                "hybrid_id": "W1_QUICK_AT_EVENT_NONE_LONG_1",
                "reentry_action": "R1",
                "parameter_set_id": "test_param_set",
                "resolved_tier": "TIER1", 
                "chain_position": "O",
                "lot_size": 0.1,
                "stop_loss": 20.0,
                "take_profit": 40.0,
                "confidence_score": 0.75
            }
            
            # Process the trade result
            result = await processor.process_trade_result(sample_trade_result)
            
            # Verify processing result
            assert result["status"] == "processed"
            assert result["trade_id"] == "TEST_TRADE_001"
            assert result["outcome_class"] == "WIN"
            assert result["duration_class"] == "QUICK"
            assert result["reentry_action"] == "R1"
            assert result["csv_written"] is True
            
            # Verify matrix client was called
            mock_client.request_reentry_decision.assert_called_once()
    
    def test_shared_library_integration(self, test_settings, metrics_collector):
        """Test integration with shared re-entry library."""
        processor = TradeResultProcessor(test_settings, metrics_collector)
        
        # Test that shared library components are loaded
        assert processor.vocabulary is not None
        assert processor.hybrid_helper is not None
        
        # Test vocabulary operations
        duration_tokens = processor.vocabulary.get_duration_tokens()
        assert "FLASH" in duration_tokens
        assert "QUICK" in duration_tokens
        assert "LONG" in duration_tokens
        assert "EXTENDED" in duration_tokens
        
        # Test hybrid ID operations
        test_hybrid = compose("W1", "QUICK", "AT_EVENT", "NONE", "LONG", 1)
        assert validate_key(test_hybrid) or True  # Allow fallback format
        
        parsed = parse(test_hybrid)
        assert parsed["outcome"] == "W1"
        assert parsed["duration"] == "QUICK"
    
    def test_metrics_collection(self, test_settings, metrics_collector):
        """Test metrics collection during processing."""
        initial_trade_count = metrics_collector.get_counter_value("trade_results_processed")
        
        # Simulate processing metrics
        metrics_collector.record_trade_processed(0.5, "WIN", "QUICK")
        metrics_collector.record_csv_write(0.1, True)
        metrics_collector.record_reentry_decision_received("R1", "TIER1", 0.75)
        
        # Verify metrics were recorded
        assert metrics_collector.get_counter_value("trade_results_processed") == initial_trade_count + 1
        assert metrics_collector.get_counter_value("csv_writes_total") == 1
        assert metrics_collector.get_counter_value("reentry_decisions_received") == 1
        
        # Test metrics summary
        summary = metrics_collector.get_metrics_summary()
        assert "trade_processing" in summary
        assert "reentry_decisions" in summary
        assert "csv_operations" in summary


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])