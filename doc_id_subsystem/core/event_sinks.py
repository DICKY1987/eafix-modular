# DOC_ID: DOC-SCRIPT-1007
"""
Event Sinks for Doc ID System
Provides different event output destinations
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class JSONLSink:
    """Sink that writes events to a JSONL file"""
    
    def __init__(self, output_file: Path):
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
    def write(self, event: Dict[str, Any]):
        """Write a single event to the JSONL file"""
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Failed to write event to {self.output_file}: {e}")
            
    def read_all(self):
        """Read all events from the JSONL file"""
        events = []
        if self.output_file.exists():
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            events.append(json.loads(line))
            except Exception as e:
                logger.error(f"Failed to read events from {self.output_file}: {e}")
        return events
        
    def clear(self):
        """Clear all events from the file"""
        if self.output_file.exists():
            self.output_file.unlink()


class ConsoleSink:
    """Sink that writes events to console/logger"""
    
    def __init__(self, log_level=logging.INFO):
        self.log_level = log_level
        
    def write(self, event: Dict[str, Any]):
        """Write event to logger"""
        logger.log(self.log_level, f"Event: {json.dumps(event)}")


class MemorySink:
    """Sink that stores events in memory for testing"""
    
    def __init__(self):
        self.events = []
        
    def write(self, event: Dict[str, Any]):
        """Store event in memory"""
        self.events.append(event)
        
    def read_all(self):
        """Return all stored events"""
        return self.events.copy()
        
    def clear(self):
        """Clear all stored events"""
        self.events.clear()
