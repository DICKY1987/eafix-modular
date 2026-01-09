# DOC_ID: DOC-TEST-0019
"""
Integration Tests for Transport Router Service

Tests complete file watching, validation, and routing pipeline.
"""

import pytest
import asyncio
import sys
import tempfile
import csv
import hashlib
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directory to path to import service modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Add contracts to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "contracts"))

from services.transport_router.src.config import Settings
from services.transport_router.src.validator import IntegrityValidator
from services.transport_router.src.router import CSVRouter
from services.transport_router.src.watcher import FileWatcher
from services.transport_router.src.metrics import MetricsCollector
from contracts.models import ActiveCalendarSignal, ReentryDecision


class TestTransportRouterIntegration:
    """Test complete transport router integration."""
    
    @pytest.fixture
    def test_settings(self):
        """Create test settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.output_directory = temp_dir
            settings.dead_letter_directory = str(Path(temp_dir) / "dead-letters")
            
            # Create watched directories
            watched_dir1 = Path(temp_dir) / "watched1"
            watched_dir2 = Path(temp_dir) / "watched2"
            watched_dir1.mkdir()
            watched_dir2.mkdir()
            
            settings.watched_directories = [str(watched_dir1), str(watched_dir2)]
            settings.file_watching_enabled = True
            settings.validate_all_files = True
            settings.routing_enabled = True
            
            # Point to actual contracts location
            project_root = Path(__file__).parent.parent.parent.parent
            settings.contracts_directory = str(project_root / "contracts")
            settings.shared_library_path = str(project_root / "shared" / "reentry")
            
            yield settings
    
    @pytest.fixture
    def metrics_collector(self):
        """Create metrics collector."""
        return MetricsCollector()
    
    def create_test_csv(self, file_path: Path, file_type: str, rows_count: int = 3) -> None:
        """Create a test CSV file with proper format."""
        if file_type == "ActiveCalendarSignal":
            header = [
                'file_seq', 'checksum_sha256', 'timestamp',
                'calendar_id', 'symbol', 'impact_level', 'proximity_state',
                'anticipation_event', 'direction_bias', 'confidence_score'
            ]
            
            rows = []
            for i in range(rows_count):
                row_data = {
                    'file_seq': str(i + 1),
                    'timestamp': datetime.utcnow().isoformat(),
                    'calendar_id': 'CAL8_USD_NFP_H',
                    'symbol': 'EURUSD',
                    'impact_level': 'HIGH',
                    'proximity_state': 'IMMEDIATE',
                    'anticipation_event': 'true',
                    'direction_bias': 'BULLISH',
                    'confidence_score': '0.75'
                }
                
                # Compute checksum
                ordered_values = []
                for key in sorted(row_data.keys()):
                    if key != 'checksum_sha256':
                        ordered_values.append(str(row_data[key]))
                
                row_string = '|'.join(ordered_values)
                checksum = hashlib.sha256(row_string.encode('utf-8')).hexdigest()
                row_data['checksum_sha256'] = checksum
                
                rows.append(row_data)
        
        elif file_type == "ReentryDecision":
            header = [
                'file_seq', 'checksum_sha256', 'timestamp',
                'trade_id', 'hybrid_id', 'symbol', 'outcome_class', 'duration_class',
                'reentry_action', 'parameter_set_id', 'resolved_tier', 'chain_position',
                'lot_size', 'stop_loss', 'take_profit'
            ]
            
            rows = []
            for i in range(rows_count):
                row_data = {
                    'file_seq': str(i + 1),
                    'timestamp': datetime.utcnow().isoformat(),
                    'trade_id': f'TEST_TRADE_{i:03d}',
                    'hybrid_id': 'W1_QUICK_AT_EVENT_NONE_LONG_1',
                    'symbol': 'EURUSD',
                    'outcome_class': 'WIN',
                    'duration_class': 'QUICK',
                    'reentry_action': 'R1',
                    'parameter_set_id': 'test_param_set',
                    'resolved_tier': 'TIER1',
                    'chain_position': 'O',
                    'lot_size': '0.1',
                    'stop_loss': '20.0',
                    'take_profit': '40.0'
                }
                
                # Compute checksum
                ordered_values = []
                for key in sorted(row_data.keys()):
                    if key != 'checksum_sha256':
                        ordered_values.append(str(row_data[key]))
                
                row_string = '|'.join(ordered_values)
                checksum = hashlib.sha256(row_string.encode('utf-8')).hexdigest()
                row_data['checksum_sha256'] = checksum
                
                rows.append(row_data)
        
        # Write CSV file
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            
            for row_data in rows:
                row = [row_data[col] for col in header]
                writer.writerow(row)
    
    @pytest.mark.asyncio
    async def test_integrity_validator(self, test_settings, metrics_collector):
        """Test CSV file integrity validation."""
        validator = IntegrityValidator(test_settings, metrics_collector)
        await validator.start()
        
        # Create test CSV file
        test_file = Path(test_settings.output_directory) / "test_active_calendar_signals.csv"
        self.create_test_csv(test_file, "ActiveCalendarSignal", 5)
        
        # Test validation
        result = await validator.validate_file(test_file, "ActiveCalendarSignal")
        
        assert result["valid"] is True
        assert result["row_count"] == 5
        assert "checksum" in result["checks_performed"]
        assert "sequence" in result["checks_performed"] 
        assert "schema" in result["checks_performed"]
        
        # Test checksum validation details
        checksum_result = result.get("checksum_validation", {})
        assert checksum_result["valid"] is True
        assert checksum_result["checksum_success_rate"] == 1.0
        
        # Test sequence validation details
        sequence_result = result.get("sequence_validation", {})
        assert sequence_result["valid"] is True
        assert sequence_result["is_monotonic"] is True
        
        # Test schema validation details
        schema_result = result.get("schema_validation", {})
        assert schema_result["valid"] is True
        assert schema_result["schema_success_rate"] == 1.0
        
        await validator.stop()
    
    @pytest.mark.asyncio
    async def test_csv_router(self, test_settings, metrics_collector):
        """Test CSV file routing to downstream services."""
        router = CSVRouter(test_settings, metrics_collector)
        
        # Mock HTTP clients
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock successful responses
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success"}
            mock_client.post.return_value = mock_response
            mock_client.get.return_value = mock_response  # For health checks
            
            await router.start()
            
            # Create test file
            test_file = Path(test_settings.output_directory) / "active_calendar_signals_test.csv"
            self.create_test_csv(test_file, "ActiveCalendarSignal")
            
            # Test routing
            result = await router.route_file(test_file, "ActiveCalendarSignal")
            
            assert result["success"] is True
            assert result["file_type"] == "ActiveCalendarSignal"
            assert result["successful_routes"] > 0
            
            # Check that services were called
            expected_services = test_settings.default_routing_rules.get("ActiveCalendarSignal", [])
            assert result["total_destinations"] == len(expected_services)
            
            await router.stop()
    
    @pytest.mark.asyncio
    async def test_file_watcher(self, test_settings, metrics_collector):
        """Test file system watching."""
        watcher = FileWatcher(test_settings, metrics_collector)
        await watcher.start()
        
        # Test scanning existing files
        watched_dir = Path(test_settings.watched_directories[0])
        test_csv = watched_dir / "existing_file.csv"
        self.create_test_csv(test_csv, "ReentryDecision")
        
        existing_files = await watcher.scan_existing_files()
        assert len(existing_files) >= 1
        assert any("existing_file.csv" in f["path"] for f in existing_files)
        
        # Test watched directory info
        directory_info = await watcher.get_watched_directories()
        assert len(directory_info) == len(test_settings.watched_directories)
        assert all(d["exists"] for d in directory_info)
        
        await watcher.stop()
    
    @pytest.mark.asyncio
    async def test_end_to_end_processing(self, test_settings, metrics_collector):
        """Test complete end-to-end file processing pipeline."""
        # Initialize components
        validator = IntegrityValidator(test_settings, metrics_collector)
        router = CSVRouter(test_settings, metrics_collector)
        
        await validator.start()
        
        # Mock router's HTTP clients
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock successful responses
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success"}
            mock_client.post.return_value = mock_response
            mock_client.get.return_value = mock_response
            
            await router.start()
            
            # Create test file
            test_file = Path(test_settings.watched_directories[0]) / "reentry_decisions_test.csv"
            self.create_test_csv(test_file, "ReentryDecision", 10)
            
            # Step 1: Validate file
            validation_result = await validator.validate_file(test_file, "ReentryDecision")
            assert validation_result["valid"] is True
            
            # Step 2: Route file
            routing_result = await router.route_file(test_file, "ReentryDecision")
            assert routing_result["success"] is True
            
            # Verify the complete pipeline worked
            assert validation_result["row_count"] == 10
            assert routing_result["successful_routes"] > 0
            
            await router.stop()
        
        await validator.stop()
    
    def test_file_type_determination(self, test_settings, metrics_collector):
        """Test file type determination from filename."""
        from services.transport_router.src.main import TransportRouterService
        
        service = TransportRouterService(test_settings, metrics_collector, None)
        
        # Test different file types
        test_cases = [
            ("active_calendar_signals_20240910.csv", "ActiveCalendarSignal"),
            ("reentry_decisions_20240910_143000.csv", "ReentryDecision"),
            ("trade_results_latest.csv", "TradeResult"),
            ("health_metrics_system.csv", "HealthMetric"),
            ("unknown_file.csv", None)
        ]
        
        for filename, expected_type in test_cases:
            file_path = Path(filename)
            determined_type = service._determine_file_type(file_path)
            assert determined_type == expected_type
    
    def test_validation_with_corrupted_data(self, test_settings, metrics_collector):
        """Test validation behavior with corrupted CSV data."""
        validator = IntegrityValidator(test_settings, metrics_collector)
        
        # Create CSV with bad checksums
        test_file = Path(test_settings.output_directory) / "corrupted_test.csv"
        
        header = [
            'file_seq', 'checksum_sha256', 'timestamp',
            'calendar_id', 'symbol', 'impact_level', 'proximity_state',
            'anticipation_event', 'direction_bias', 'confidence_score'
        ]
        
        # Write CSV with intentionally wrong checksums
        with open(test_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            
            # Row with bad checksum
            writer.writerow([
                '1', 'bad_checksum_12345', datetime.utcnow().isoformat(),
                'CAL8_USD_NFP_H', 'EURUSD', 'HIGH', 'IMMEDIATE',
                'true', 'BULLISH', '0.75'
            ])
        
        # Test validation should fail
        result = asyncio.run(validator.validate_file(test_file, "ActiveCalendarSignal"))
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "checksum" in result["checks_performed"]
    
    def test_metrics_collection(self, test_settings, metrics_collector):
        """Test metrics collection during operations."""
        initial_validations = metrics_collector.get_counter_value("validations_performed")
        
        # Simulate metrics recording
        metrics_collector.record_file_validation(0.5, True, "ActiveCalendarSignal")
        metrics_collector.record_file_routing(1.0, True, "ReentryDecision")
        metrics_collector.record_service_delivery("risk-manager", 0.2, True)
        
        # Check metrics were recorded
        assert metrics_collector.get_counter_value("validations_performed") == initial_validations + 1
        assert metrics_collector.get_counter_value("routing_attempts") == 1
        assert metrics_collector.get_counter_value("service_deliveries") == 1
        
        # Test metrics summary
        summary = metrics_collector.get_metrics_summary()
        assert "file_processing" in summary
        assert "validation" in summary
        assert "routing" in summary
        assert "system" in summary


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])