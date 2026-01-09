#!/usr/bin/env python3
# DOC_ID: DOC-SERVICE-0116
"""
Manual Economic Calendar Event Simulator
Creates synthetic calendar events to test the complete signal flow
"""

import json
import csv
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class CalendarEventSimulator:
    """Simulates economic calendar events for testing"""
    
    def __init__(self, csv_dir: str = None):
        self.csv_dir = Path(csv_dir) if csv_dir else Path.cwd() / "test_data"
        self.csv_dir.mkdir(exist_ok=True)
        self.file_seq = 1
        
    def generate_cal8_id(self, region: str, country: str, impact: str, 
                        event_type: str, version: str = "1", revision: str = "0") -> str:
        """Generate CAL8 identifier: R1C2I1E2V1F1"""
        return f"{region}{country}{impact}{event_type}{version}{revision}"
    
    def generate_hybrid_id(self, cal8: str, generation: str = "O", 
                          signal: str = "ECO_HIGH_USD", duration: str = "FL",
                          outcome: str = "O1", proximity: str = "IM", 
                          symbol: str = "EURUSD") -> str:
        """Generate Hybrid ID"""
        return f"{cal8}-{generation}-{signal}-{duration}-{outcome}-{proximity}-{symbol}"
    
    def create_test_event(self, event_config: Dict) -> Dict:
        """Create a single test calendar event"""
        now = datetime.utcnow()
        event_time = now + timedelta(minutes=event_config.get('minutes_from_now', 30))
        
        # Generate CAL8 ID
        cal8 = self.generate_cal8_id(
            region=event_config.get('region', 'A'),
            country=event_config.get('country', 'US'),
            impact=event_config.get('impact', 'H'),
            event_type=event_config.get('event_type', 'NF')
        )
        
        # Generate CAL5 (legacy alias)
        cal5 = cal8[:5]
        
        event = {
            'symbol': event_config.get('symbol', 'EURUSD'),
            'cal8': cal8,
            'cal5': cal5,
            'signal_type': event_config.get('signal_type', 'ECO_HIGH_USD'),
            'proximity': event_config.get('proximity', 'SH'),  # SH = Short-term
            'event_time_utc': event_time.isoformat() + 'Z',
            'state': event_config.get('state', 'SCHEDULED'),
            'priority_weight': event_config.get('priority_weight', 1.0),
            'file_seq': self.file_seq,
            'created_at_utc': now.isoformat() + 'Z',
        }
        
        # Add checksum
        event_str = json.dumps(event, sort_keys=True)
        event['checksum_sha256'] = hashlib.sha256(event_str.encode()).hexdigest()
        
        return event
    
    def write_active_calendar_signals(self, events: List[Dict]) -> str:
        """Write events to active_calendar_signals.csv with atomic write"""
        temp_file = self.csv_dir / "active_calendar_signals.csv.tmp"
        final_file = self.csv_dir / "active_calendar_signals.csv"
        
        # CSV headers as per spec
        headers = [
            'symbol', 'cal8', 'cal5', 'signal_type', 'proximity', 
            'event_time_utc', 'state', 'priority_weight', 'file_seq',
            'created_at_utc', 'checksum_sha256'
        ]
        
        with open(temp_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(events)
        
        # Atomic rename
        temp_file.rename(final_file)
        self.file_seq += 1
        
        return str(final_file)

    def simulate_event_lifecycle(self, symbol: str = "EURUSD", 
                                minutes_ahead: int = 30) -> List[str]:
        """Simulate complete event lifecycle: SCHEDULED -> ANTICIPATION -> ACTIVE -> COOLDOWN -> EXPIRED"""
        
        states = [
            ('SCHEDULED', 'LG', minutes_ahead),      # Long-term proximity
            ('ANTICIPATION', 'SH', 15),              # Short-term proximity  
            ('ACTIVE', 'IM', 0),                     # Immediate proximity
            ('COOLDOWN', 'CD', -5),                  # Cooldown phase
            ('EXPIRED', 'EX', -30)                   # Expired
        ]
        
        created_files = []
        
        for state, proximity, time_offset in states:
            event_config = {
                'symbol': symbol,
                'region': 'A',
                'country': 'US', 
                'impact': 'H',
                'event_type': 'NF',  # Non-farm payrolls
                'signal_type': 'ECO_HIGH_USD',
                'state': state,
                'proximity': proximity,
                'minutes_from_now': time_offset,
                'priority_weight': 1.0 if state == 'ACTIVE' else 0.8
            }
            
            event = self.create_test_event(event_config)
            file_path = self.write_active_calendar_signals([event])
            created_files.append(file_path)
            
            print(f"Created {state} event: {file_path}")
            
        return created_files

    def create_multiple_events(self, event_configs: List[Dict]) -> str:
        """Create multiple events in single CSV file"""
        events = []
        for config in event_configs:
            events.append(self.create_test_event(config))
        
        return self.write_active_calendar_signals(events)


def main():
    """Demo script showing different test scenarios"""
    simulator = CalendarEventSimulator()
    
    print("=== Economic Calendar Event Simulator ===\n")
    
    # Scenario 1: Single high-impact USD event
    print("1. Creating single high-impact USD Non-Farm Payrolls event...")
    single_event = simulator.create_test_event({
        'symbol': 'EURUSD',
        'region': 'A',
        'country': 'US',
        'impact': 'H',
        'event_type': 'NF',
        'signal_type': 'ECO_HIGH_USD',
        'state': 'SCHEDULED',
        'proximity': 'SH',
        'minutes_from_now': 30
    })
    file1 = simulator.write_active_calendar_signals([single_event])
    print(f"   Created: {file1}\n")
    
    # Scenario 2: Multiple currency events  
    print("2. Creating multiple currency events...")
    multi_events = [
        {
            'symbol': 'EURUSD',
            'region': 'E', 'country': 'EU', 'impact': 'H', 'event_type': 'CP',
            'signal_type': 'ECO_HIGH_EUR', 'minutes_from_now': 45
        },
        {
            'symbol': 'GBPUSD', 
            'region': 'E', 'country': 'GB', 'impact': 'M', 'event_type': 'PM',
            'signal_type': 'ECO_MED_GBP', 'minutes_from_now': 60
        },
        {
            'symbol': 'USDJPY',
            'region': 'P', 'country': 'JP', 'impact': 'H', 'event_type': 'RD', 
            'signal_type': 'ECO_HIGH_JPY', 'minutes_from_now': 90
        }
    ]
    file2 = simulator.create_multiple_events(multi_events)
    print(f"   Created: {file2}\n")
    
    # Scenario 3: Complete lifecycle simulation
    print("3. Simulating complete event lifecycle...")
    lifecycle_files = simulator.simulate_event_lifecycle('EURUSD', 120)
    print(f"   Created {len(lifecycle_files)} lifecycle files\n")
    
    print("=== Test Files Created ===")
    print("You can now:")
    print("1. Monitor the system's response to these events")
    print("2. Check if signals appear in the Signals Tab")
    print("3. Verify Economic Calendar Tab shows the events")
    print("4. Confirm decisions flow to reentry_decisions.csv")
    print("5. Watch for MT4 execution")


if __name__ == "__main__":
    main()
