# doc_id: DOC-TEST-0210
# DOC_ID: DOC-TEST-0011
"""
Tests for Calendar Ingestor Service
"""

import pytest
import asyncio
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Add parent directory to path to import service modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from services.calendar_ingestor.src.ingestor import CalendarIngestor
from services.calendar_ingestor.src.config import Settings
from services.calendar_ingestor.src.metrics import MetricsCollector


class TestCalendarIngestor:
    """Test calendar ingestor functionality"""
    
    @pytest.fixture
    def test_settings(self):
        """Create test settings"""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.output_directory = temp_dir
            settings.redis_url = "redis://localhost:6379"
            yield settings
    
    @pytest.fixture
    def metrics_collector(self):
        """Create metrics collector"""
        return MetricsCollector()
    
    @pytest.fixture
    async def calendar_ingestor(self, test_settings, metrics_collector):
        """Create calendar ingestor instance"""
        ingestor = CalendarIngestor(test_settings, metrics_collector)
        
        # Mock Redis client
        ingestor.redis_client = AsyncMock()
        ingestor.redis_client.ping = AsyncMock()
        ingestor.redis_client.publish = AsyncMock()
        ingestor.redis_client.close = AsyncMock()
        
        await ingestor.start()
        yield ingestor
        await ingestor.stop()
    
    @pytest.mark.asyncio
    async def test_process_high_impact_event(self, calendar_ingestor):
        """Test processing of high impact calendar event"""
        # High impact NFP event
        event = {
            "name": "Non-Farm Payrolls",
            "currency": "USD",
            "impact": "HIGH",
            "datetime": datetime.now(timezone.utc).isoformat(),
            "forecast": "150K",
            "previous": "140K"
        }
        
        result = await calendar_ingestor.process_calendar_event(event)
        
        assert result["status"] == "success"
        assert result["signals_generated"] > 0
        assert "CAL8_USD_NFP_H" in result["calendar_id"]
        assert result["proximity_state"] in ["PRE_1H", "AT_EVENT", "POST_30M"]
    
    @pytest.mark.asyncio  
    async def test_process_medium_impact_event(self, calendar_ingestor):
        """Test processing of medium impact calendar event"""
        event = {
            "name": "PMI Manufacturing",
            "currency": "EUR",
            "impact": "MEDIUM", 
            "datetime": datetime.now(timezone.utc).isoformat()
        }
        
        result = await calendar_ingestor.process_calendar_event(event)
        
        assert result["status"] == "success"
        assert "CAL5" in result["calendar_id"]
    
    @pytest.mark.asyncio
    async def test_calendar_id_determination(self, calendar_ingestor):
        """Test calendar ID assignment logic"""
        # High impact event should get CAL8
        high_event = {
            "name": "FOMC Meeting Decision",
            "currency": "USD", 
            "impact": "HIGH"
        }
        
        cal_id = calendar_ingestor._determine_calendar_id(high_event)
        assert cal_id.startswith("CAL8_USD_")
        assert cal_id.endswith("_H")
        
        # Medium impact event should get CAL5
        med_event = {
            "name": "Retail Sales",
            "currency": "GBP",
            "impact": "MEDIUM"
        }
        
        cal_id = calendar_ingestor._determine_calendar_id(med_event)
        assert cal_id.startswith("CAL5_")
    
    @pytest.mark.asyncio
    async def test_proximity_state_determination(self, calendar_ingestor):
        """Test proximity state calculation"""
        current_time = datetime.now(timezone.utc)
        
        # Event happening now should be AT_EVENT
        proximity = calendar_ingestor._determine_proximity_state(current_time, current_time)
        assert proximity == "AT_EVENT"
        
        # Event 30 minutes ago should be PRE_1H  
        from datetime import timedelta
        past_time = current_time - timedelta(minutes=30)
        proximity = calendar_ingestor._determine_proximity_state(current_time, past_time)
        assert proximity == "PRE_1H"
    
    def test_confidence_score_calculation(self, calendar_ingestor):
        """Test confidence score calculation"""
        # High impact event should have higher confidence
        high_event = {"impact": "HIGH", "name": "Non-Farm Payrolls"}
        high_confidence = calendar_ingestor._calculate_confidence_score(high_event, "AT_EVENT")
        
        med_event = {"impact": "MEDIUM", "name": "Retail Sales"}
        med_confidence = calendar_ingestor._calculate_confidence_score(med_event, "AT_EVENT")
        
        assert high_confidence > med_confidence
        assert 0.0 <= high_confidence <= 1.0
        assert 0.0 <= med_confidence <= 1.0
    
    def test_checksum_computation(self, calendar_ingestor):
        """Test checksum computation for CSV rows"""
        row_data = {
            "file_seq": 1,
            "timestamp": "2024-09-10T14:30:00Z",
            "calendar_id": "CAL8_USD_NFP_H",
            "symbol": "EURUSD"
        }
        
        checksum1 = calendar_ingestor._compute_row_checksum(row_data)
        checksum2 = calendar_ingestor._compute_row_checksum(row_data)
        
        # Same data should produce same checksum
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex string length
        
        # Different data should produce different checksum
        row_data["symbol"] = "GBPUSD"
        checksum3 = calendar_ingestor._compute_row_checksum(row_data)
        assert checksum1 != checksum3
    
    @pytest.mark.asyncio
    async def test_csv_file_creation(self, calendar_ingestor, test_settings):
        """Test that CSV files are created with proper format"""
        event = {
            "name": "GDP",
            "currency": "EUR",
            "impact": "HIGH",
            "datetime": datetime.now(timezone.utc).isoformat()
        }
        
        result = await calendar_ingestor.process_calendar_event(event)
        
        # Check that CSV files were created
        output_dir = Path(test_settings.output_directory)
        csv_files = list(output_dir.glob("active_calendar_signals_*.csv"))
        assert len(csv_files) > 0
        
        # Check CSV content
        csv_file = csv_files[0]
        content = csv_file.read_text()
        
        # Should have header row
        lines = content.strip().split('\n')
        assert len(lines) >= 2  # Header + at least one data row
        
        # Header should contain required fields
        header = lines[0].split(',')
        required_fields = [
            'file_seq', 'checksum_sha256', 'timestamp', 'calendar_id',
            'symbol', 'impact_level', 'proximity_state', 'anticipation_event',
            'direction_bias', 'confidence_score'
        ]
        
        for field in required_fields:
            assert field in header
    
    @pytest.mark.asyncio
    async def test_contract_validation(self, calendar_ingestor):
        """Test that generated signals pass contract validation"""
        event = {
            "name": "Consumer Price Index",
            "currency": "USD", 
            "impact": "HIGH",
            "datetime": datetime.now(timezone.utc).isoformat()
        }
        
        # This should not raise validation errors
        result = await calendar_ingestor.process_calendar_event(event)
        assert result["status"] == "success"
        
        # Check active signals are valid
        active_signals = await calendar_ingestor.get_active_signals()
        assert len(active_signals) > 0
        
        # Each signal should have all required fields
        for signal in active_signals:
            assert "file_seq" in signal
            assert "checksum_sha256" in signal  
            assert "calendar_id" in signal
            assert signal["impact_level"] in ["HIGH", "MEDIUM", "LOW"]
            assert signal["proximity_state"] in ["PRE_1H", "AT_EVENT", "POST_30M"]
            assert 0.0 <= signal["confidence_score"] <= 1.0


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])