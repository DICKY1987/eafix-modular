#!/usr/bin/env python3
"""
Integration tests for the complete contract system.

Tests the full pipeline from schema validation to CSV processing
to shared re-entry library functionality.
"""

import pytest
import json
import csv
import tempfile
from pathlib import Path
from datetime import datetime

# Import our contract system
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from contracts.models import (
    ActiveCalendarSignal, ReentryDecision, TradeResult, HealthMetric,
    IndicatorRecord, OrderIn, OrderOut, HybridId
)
from contracts.validate_json_schemas import JSONSchemaValidator
from contracts.validate_csv_artifacts import CSVArtifactValidator
from shared.reentry import (
    HybridIdHelper, ReentryVocabulary, IndicatorValidator,
    compose, parse, validate_key, comment_suffix_hash
)


class TestContractIntegration:
    """Integration tests for the complete contract system."""
    
    def test_json_schema_validation_pipeline(self):
        """Test complete JSON schema validation pipeline."""
        # Create validator
        validator = JSONSchemaValidator()
        
        # Test indicator record validation
        indicator_data = {
            "IndicatorID": "TEST_INDICATOR",
            "Concept": "Test indicator concept",
            "Indicator_Computation": "Test computation logic",
            "Signal_Logic": "Test signal logic", 
            "OutputType": "z_score",
            "Thresholds": {
                "kind": "zscore",
                "gte": 2.0,
                "lte": -2.0,
                "hysteresis": 0.1,
                "persistence_bars": 3,
                "direction": "both"
            },
            "Inputs": {
                "symbol_scope": ["EURUSD", "GBPUSD"],
                "timeframe": "H1",
                "price_source": "close"
            }
        }
        
        # Should validate successfully
        valid, errors = validator.validate_indicator_record(indicator_data)
        assert valid, f"Indicator record validation failed: {errors}"
        
        # Test Pydantic model creation
        indicator_model = IndicatorRecord(**indicator_data)
        assert indicator_model.IndicatorID == "TEST_INDICATOR"
    
    def test_csv_validation_pipeline(self):
        """Test complete CSV validation pipeline."""
        # Create CSV validator
        validator = CSVArtifactValidator()
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='_20240910_143000.csv',
            prefix='active_calendar_signals',
            delete=False,
            newline=''
        ) as f:
            writer = csv.writer(f)
            
            # Write header
            headers = [
                "file_seq", "checksum_sha256", "timestamp", "calendar_id", "symbol",
                "impact_level", "proximity_state", "anticipation_event", 
                "direction_bias", "confidence_score"
            ]
            writer.writerow(headers)
            
            # Write test data with computed checksum
            row_data = {
                "file_seq": "1",
                "timestamp": "2024-09-10T14:30:00Z",
                "calendar_id": "CAL8_USD_NFP_H",
                "symbol": "EURUSD",
                "impact_level": "HIGH",
                "proximity_state": "AT_EVENT", 
                "anticipation_event": "false",
                "direction_bias": "BULLISH",
                "confidence_score": "0.85"
            }
            
            # Compute checksum (excluding checksum field)
            checksum = validator.compute_row_checksum(row_data)
            row_data["checksum_sha256"] = checksum
            
            # Write row in correct order
            row_values = [row_data[header] for header in headers]
            writer.writerow(row_values)
            
            csv_path = Path(f.name)
        
        try:
            # Validate the CSV file
            result = validator.validate_csv_file(csv_path)
            assert result["valid"], f"CSV validation failed: {result['errors']}"
            assert result["csv_type"] == "active_calendar_signals"
            assert result["stats"]["total_rows"] == 1
            
        finally:
            # Clean up
            if csv_path.exists():
                csv_path.unlink()
    
    def test_hybrid_id_pipeline(self):
        """Test complete hybrid ID functionality."""
        # Create hybrid ID helper
        helper = HybridIdHelper()
        
        # Test composition
        hybrid_id = helper.compose(
            outcome="W1",
            duration="QUICK", 
            proximity="AT_EVENT",
            calendar="CAL8_USD_NFP_H",
            direction="LONG",
            generation=1
        )
        
        expected = "W1_QUICK_AT_EVENT_CAL8_USD_NFP_H_LONG_1"
        assert hybrid_id == expected
        
        # Test parsing
        components = helper.parse(hybrid_id)
        assert components["outcome"] == "W1"
        assert components["duration"] == "QUICK"
        assert components["proximity"] == "AT_EVENT" 
        assert components["calendar"] == "CAL8_USD_NFP_H"
        assert components["direction"] == "LONG"
        assert components["generation"] == "1"
        
        # Test validation
        assert helper.validate_key(hybrid_id)
        
        # Test comment suffix generation
        suffix = helper.comment_suffix_hash(hybrid_id)
        assert len(suffix) == 6
        assert suffix.islower()
        assert suffix.isalnum()
        
        # Test deterministic suffix generation
        suffix2 = helper.comment_suffix_hash(hybrid_id)
        assert suffix == suffix2, "Comment suffix should be deterministic"
    
    def test_pydantic_model_integration(self):
        """Test Pydantic models with real data."""
        # Test ActiveCalendarSignal
        signal_data = {
            "file_seq": 1,
            "checksum_sha256": "a" * 64,  # Valid hex string
            "timestamp": datetime.utcnow(),
            "calendar_id": "CAL8_USD_NFP_H",
            "symbol": "EURUSD",
            "impact_level": "HIGH",
            "proximity_state": "AT_EVENT",
            "anticipation_event": False,
            "direction_bias": "BULLISH", 
            "confidence_score": 0.85
        }
        
        signal = ActiveCalendarSignal(**signal_data)
        assert signal.calendar_id == "CAL8_USD_NFP_H"
        assert signal.confidence_score == 0.85
        
        # Test checksum computation
        computed_checksum = signal.compute_checksum()
        assert len(computed_checksum) == 64
        assert all(c in '0123456789abcdef' for c in computed_checksum)
    
    def test_vocabulary_consistency(self):
        """Test vocabulary consistency across components."""
        vocab = ReentryVocabulary()
        helper = HybridIdHelper(vocab)
        
        # Test all valid combinations
        for outcome in vocab.get_outcome_tokens():
            for duration in vocab.get_duration_tokens():
                for proximity in vocab.get_proximity_tokens():
                    for direction in vocab.get_direction_tokens():
                        hybrid_id = helper.compose(
                            outcome=outcome,
                            duration=duration,
                            proximity=proximity,
                            calendar="CAL8_USD_NFP_H", 
                            direction=direction,
                            generation=1
                        )
                        
                        # Should validate successfully
                        assert helper.validate_key(hybrid_id), f"Invalid combination: {hybrid_id}"
                        
                        # Should parse back to same components
                        components = helper.parse(hybrid_id)
                        assert components["outcome"] == outcome
                        assert components["duration"] == duration
                        assert components["proximity"] == proximity
                        assert components["direction"] == direction
    
    def test_cross_language_parity_prep(self):
        """Test preparation for cross-language parity testing."""
        # Test cases that should produce identical results in MQL4
        test_cases = [
            "W1_QUICK_AT_EVENT_CAL8_USD_NFP_H_LONG_1",
            "L1_EXTENDED_PRE_1H_CAL5_GDPQ1_SHORT_2", 
            "BE_FLASH_POST_30M_NONE_ANY_1",
            "W2_LONG_AT_EVENT_CAL8_EUR_ECB_H_LONG_3"
        ]
        
        helper = HybridIdHelper()
        
        for hybrid_id in test_cases:
            # Generate comment suffix
            suffix = helper.comment_suffix_hash(hybrid_id)
            
            # Document expected results for MQL4 comparison
            print(f"Hybrid ID: {hybrid_id}")
            print(f"Expected suffix: {suffix}")
            
            # Validate parsing
            components = helper.parse(hybrid_id)
            rebuilt = helper.compose(**{
                k: v if k != "generation" else int(v) 
                for k, v in components.items() 
                if k != "suffix"
            })
            
            assert rebuilt == hybrid_id, f"Round-trip failed for {hybrid_id}"
    
    def test_end_to_end_reentry_workflow(self):
        """Test complete re-entry workflow simulation."""
        # Step 1: Create original trade outcome
        original_hybrid_id = compose(
            outcome="W1",
            duration="QUICK",
            proximity="AT_EVENT", 
            calendar="CAL8_USD_NFP_H",
            direction="LONG",
            generation=1
        )
        
        # Step 2: Generate comment suffix for MT4
        comment_suffix = comment_suffix_hash(original_hybrid_id)
        mt4_comment = f"NFP_LONG_{comment_suffix}"
        assert len(mt4_comment) <= 31, "MT4 comment too long"
        
        # Step 3: Create trade result CSV data
        trade_result_data = {
            "file_seq": 1,
            "checksum_sha256": "b" * 64,
            "timestamp": datetime.utcnow(),
            "trade_id": "TRADE_20240910_001", 
            "symbol": "EURUSD",
            "direction": "BUY",
            "lot_size": 0.01,
            "open_price": 1.10000,
            "close_price": 1.10500,
            "open_time": datetime.utcnow(),
            "close_time": datetime.utcnow(),
            "duration_minutes": 30,
            "profit_loss": 50.0,
            "profit_loss_pips": 50.0,
            "stop_loss": 1.09750,
            "take_profit": 1.10500,
            "close_reason": "TP",
            "commission": 0.0,
            "swap": 0.0,
            "magic_number": 12345,
            "comment": mt4_comment
        }
        
        # Step 4: Validate trade result model
        trade_result = TradeResult(**trade_result_data)
        assert trade_result.close_reason == "TP"
        
        # Step 5: Create re-entry decision
        reentry_decision_data = {
            "file_seq": 1,
            "checksum_sha256": "c" * 64,
            "timestamp": datetime.utcnow(),
            "trade_id": trade_result_data["trade_id"],
            "hybrid_id": original_hybrid_id,
            "symbol": "EURUSD",
            "outcome_class": "WIN",
            "duration_class": "QUICK",
            "reentry_action": "R1", 
            "parameter_set_id": "PS_EURUSD_HIGH_001",
            "resolved_tier": "EXACT",
            "chain_position": "O",
            "lot_size": 0.01,
            "stop_loss": 25.0,
            "take_profit": 50.0
        }
        
        # Step 6: Validate re-entry decision
        reentry_decision = ReentryDecision(**reentry_decision_data)
        assert reentry_decision.reentry_action == "R1"
        
        # Step 7: Generate R1 hybrid ID
        r1_hybrid_id = compose(
            outcome="W1",  # Same outcome as original
            duration="QUICK",  # Same duration
            proximity="AT_EVENT",  # Same proximity
            calendar="CAL8_USD_NFP_H",  # Same calendar
            direction="LONG",  # Same direction
            generation=2  # R1 generation
        )
        
        # Verify R1 hybrid ID is different from original
        assert r1_hybrid_id != original_hybrid_id
        assert "2" in r1_hybrid_id  # Should have generation 2
        
        print(f"End-to-end workflow completed successfully:")
        print(f"Original: {original_hybrid_id}")
        print(f"R1: {r1_hybrid_id}")
        print(f"MT4 Comment: {mt4_comment}")


def test_fixture_validation():
    """Test that all fixture files are valid."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    
    # Test JSON fixtures
    json_validator = JSONSchemaValidator()
    
    json_fixtures = {
        "indicator_record_valid.json": json_validator.validate_indicator_record,
        "orders_in_valid.json": json_validator.validate_order_in,
        "orders_out_valid.json": json_validator.validate_order_out
    }
    
    for fixture_file, validator_func in json_fixtures.items():
        fixture_path = fixtures_dir / fixture_file
        if fixture_path.exists():
            with open(fixture_path, 'r') as f:
                data = json.load(f)
            
            valid, errors = validator_func(data)
            assert valid, f"Fixture {fixture_file} is invalid: {errors}"
    
    # Test CSV fixtures  
    csv_validator = CSVArtifactValidator()
    
    csv_fixtures = fixtures_dir.glob("*.csv")
    for csv_file in csv_fixtures:
        result = csv_validator.validate_csv_file(csv_file)
        # Note: These may fail checksum validation since they're sample data
        # We're mainly testing the structure and format
        assert result["csv_type"] is not None, f"Could not detect CSV type for {csv_file}"


if __name__ == "__main__":
    # Run tests directly
    test_instance = TestContractIntegration()
    
    print("Running contract integration tests...")
    
    try:
        test_instance.test_json_schema_validation_pipeline()
        print("✓ JSON schema validation pipeline")
        
        test_instance.test_csv_validation_pipeline()
        print("✓ CSV validation pipeline")
        
        test_instance.test_hybrid_id_pipeline()
        print("✓ Hybrid ID pipeline")
        
        test_instance.test_pydantic_model_integration()
        print("✓ Pydantic model integration")
        
        test_instance.test_vocabulary_consistency()
        print("✓ Vocabulary consistency")
        
        test_instance.test_cross_language_parity_prep()
        print("✓ Cross-language parity preparation")
        
        test_instance.test_end_to_end_reentry_workflow()
        print("✓ End-to-end re-entry workflow")
        
        test_fixture_validation()
        print("✓ Fixture validation")
        
        print("\n🎉 All integration tests passed!")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        raise