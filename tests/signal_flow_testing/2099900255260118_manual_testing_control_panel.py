#!/usr/bin/env python3
# doc_id: DOC-TEST-0075
# DOC_ID: DOC-SERVICE-0122
"""
Manual Testing Control Panel
Interactive tool for testing all signal system branches
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import argparse


class TestingControlPanel:
    """Interactive control panel for signal system testing"""
    
    def __init__(self, mt4_data_folder: str):
        self.mt4_data_folder = Path(mt4_data_folder)
        self.eafix_dir = self.mt4_data_folder / "eafix"
        self.test_data_dir = Path.cwd() / "test_data"
        
        # Ensure directories exist
        self.eafix_dir.mkdir(parents=True, exist_ok=True)
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Import simulators
        try:
            from calendar_event_simulator import CalendarEventSimulator
            from indicator_signal_simulator import IndicatorSignalSimulator
            from signal_flow_tester import SignalFlowTester
            
            self.calendar_sim = CalendarEventSimulator(str(self.test_data_dir))
            self.indicator_sim = IndicatorSignalSimulator(str(self.test_data_dir))
            self.flow_tester = SignalFlowTester(str(self.mt4_data_folder))
            
        except ImportError as e:
            print(f"Error importing simulators: {e}")
            print("Make sure all simulator files are in the same directory")
            sys.exit(1)
    
    def display_menu(self):
        """Display main menu"""
        print("\n" + "="*60)
        print("           SIGNAL SYSTEM TESTING CONTROL PANEL")
        print("="*60)
        print("1.  📅 Economic Calendar Tests")
        print("2.  📊 Technical Indicator Tests") 
        print("3.  🔗 Communication Layer Tests")
        print("4.  🎯 End-to-End Flow Tests")
        print("5.  🔍 System Status & Monitoring")
        print("6.  ⚙️  Configuration & Setup")
        print("7.  📋 View Test History")
        print("8.  🧹 Cleanup Test Data")
        print("0.  ❌ Exit")
        print("="*60)
    
    def calendar_tests_menu(self):
        """Economic calendar testing submenu"""
        while True:
            print("\n📅 ECONOMIC CALENDAR TESTS")
            print("-" * 40)
            print("1. Single High-Impact Event (USD NFP)")
            print("2. Multiple Currency Events")
            print("3. Event Lifecycle Simulation")
            print("4. Emergency Stop/Resume Test")
            print("5. Priority Weight Testing")
            print("6. State Transition Testing")
            print("7. Custom Event Creation")
            print("0. Back to Main Menu")
            
            choice = input("\nSelect test: ").strip()
            
            if choice == "1":
                self.test_single_high_impact_event()
            elif choice == "2":
                self.test_multiple_currency_events()
            elif choice == "3":
                self.test_event_lifecycle()
            elif choice == "4":
                self.test_emergency_controls()
            elif choice == "5":
                self.test_priority_weights()
            elif choice == "6":
                self.test_state_transitions()
            elif choice == "7":
                self.create_custom_event()
            elif choice == "0":
                break
            else:
                print("❌ Invalid selection")
    
    def indicator_tests_menu(self):
        """Technical indicator testing submenu"""
        while True:
            print("\n📊 TECHNICAL INDICATOR TESTS")
            print("-" * 40)
            print("1. Moving Average Crossover")
            print("2. RSI Extreme Conditions")
            print("3. Bollinger Band Squeeze")
            print("4. Volume Spike Detection")
            print("5. Multi-Indicator Confluence")
            print("6. Custom Indicator Signal")
            print("7. Stress Test (Multiple Symbols)")
            print("8. Signal Confidence Testing")
            print("0. Back to Main Menu")
            
            choice = input("\nSelect test: ").strip()
            
            if choice == "1":
                self.test_ma_crossover()
            elif choice == "2":
                self.test_rsi_extreme()
            elif choice == "3":
                self.test_bollinger_squeeze()
            elif choice == "4":
                self.test_volume_spike()
            elif choice == "5":
                self.test_indicator_confluence()
            elif choice == "6":
                self.create_custom_indicator_signal()
            elif choice == "7":
                self.run_indicator_stress_test()
            elif choice == "8":
                self.test_signal_confidence()
            elif choice == "0":
                break
            else:
                print("❌ Invalid selection")
    
    def communication_tests_menu(self):
        """Communication layer testing submenu"""
        while True:
            print("\n🔗 COMMUNICATION LAYER TESTS")
            print("-" * 40)
            print("1. Socket Connection Test")
            print("2. CSV Integrity Check")
            print("3. File Sequence Validation")
            print("4. Checksum Verification")
            print("5. Failover Testing (Socket->CSV)")
            print("6. Heartbeat Monitoring")
            print("7. Transport Performance Test")
            print("0. Back to Main Menu")
            
            choice = input("\nSelect test: ").strip()
            
            if choice == "1":
                self.test_socket_connection()
            elif choice == "2":
                self.test_csv_integrity()
            elif choice == "3":
                self.test_file_sequences()
            elif choice == "4":
                self.test_checksums()
            elif choice == "5":
                self.test_failover()
            elif choice == "6":
                self.test_heartbeat()
            elif choice == "7":
                self.test_transport_performance()
            elif choice == "0":
                break
            else:
                print("❌ Invalid selection")
    
    def test_single_high_impact_event(self):
        """Test single high-impact event processing"""
        print("\n🧪 Testing Single High-Impact USD Event...")
        
        # Get user input for timing
        minutes = input("Minutes from now (default 30): ").strip()
        minutes = int(minutes) if minutes else 30
        
        symbol = input("Symbol (default EURUSD): ").strip() or "EURUSD"
        
        event_config = {
            'symbol': symbol,
            'currency': 'USD',
            'impact_level': 'HIGH',
            'event_code': 'NFP',
            'proximity_state': 'PRE_1H' if minutes > 5 else 'AT_EVENT',
            'minutes_from_now': minutes,
            'confidence_score': 0.85,
        }
        
        try:
            event = self.calendar_sim.create_test_event(event_config)
            file_path = self.calendar_sim.write_active_calendar_signals([event])
            
            print(f"✅ Created event: {file_path}")
            print(f"📋 Event Details:")
            print(f"   Symbol: {event['symbol']}")
            print(f"   Calendar ID: {event['calendar_id']}")
            print(f"   Proximity: {event['proximity_state']}")
            print(f"   Timestamp: {event['timestamp']}")
            print(f"   Direction Bias: {event['direction_bias']}")
            
            # Copy to MT4 directory for processing
            import shutil
            dest = self.eafix_dir / "active_calendar_signals.csv"
            shutil.copy(file_path, dest)
            print(f"📁 Copied to MT4 directory: {dest}")
            
            print("\n📊 Monitor the following:")
            print("• Economic Calendar Tab for the new event")
            print("• Signals Tab for generated signals")
            print("• System logs for processing status")
            
        except Exception as e:
            print(f"❌ Error creating event: {e}")
    
    def test_event_lifecycle(self):
        """Test complete event lifecycle"""
        print("\n🔄 Testing Complete Event Lifecycle...")
        
        symbol = input("Symbol (default EURUSD): ").strip() or "EURUSD"
        
        try:
            lifecycle_files = self.calendar_sim.simulate_event_lifecycle(symbol, 60)
            
            print(f"✅ Created {len(lifecycle_files)} lifecycle files")
            
            # Copy each file with delays to simulate real-time progression
            for i, file_path in enumerate(lifecycle_files):
                dest = self.eafix_dir / f"active_calendar_signals_{i}.csv"
                import shutil
                shutil.copy(file_path, dest)
                
                print(f"📁 Stage {i+1}: {Path(file_path).name} -> {dest.name}")
                
                if i < len(lifecycle_files) - 1:
                    delay = input(f"Press Enter to proceed to next stage (or enter delay in seconds): ").strip()
                    if delay.isdigit():
                        time.sleep(int(delay))
            
            print("\n✅ Lifecycle simulation complete")
            
        except Exception as e:
            print(f"❌ Error in lifecycle test: {e}")
    
    def test_ma_crossover(self):
        """Test moving average crossover signal"""
        print("\n📈 Testing Moving Average Crossover...")
        
        symbol = input("Symbol (default EURUSD): ").strip() or "EURUSD"
        direction = input("Direction (LONG/SHORT, default LONG): ").strip() or "LONG"
        
        try:
            signal_file = self.indicator_sim.simulate_ma_crossover(symbol, direction)
            
            print(f"✅ Created MA crossover signal: {signal_file}")
            
            # Copy to MT4 directory
            import shutil
            dest = self.eafix_dir / "indicator_signals.csv"
            shutil.copy(signal_file, dest)
            print(f"📁 Copied to MT4 directory: {dest}")
            
            print(f"\n📋 Signal Details:")
            print(f"   Symbol: {symbol}")
            print(f"   Direction: {direction}")
            print(f"   Type: MA Crossover")
            print(f"   Confidence: HIGH")
            
        except Exception as e:
            print(f"❌ Error creating MA signal: {e}")
    
    def test_indicator_confluence(self):
        """Test multi-indicator confluence"""
        print("\n🎯 Testing Multi-Indicator Confluence...")
        
        symbol = input("Symbol (default EURUSD): ").strip() or "EURUSD"
        
        try:
            signal_file = self.indicator_sim.simulate_multi_indicator_confluence(symbol)
            
            print(f"✅ Created confluence signals: {signal_file}")
            
            # Copy to MT4 directory
            import shutil
            dest = self.eafix_dir / "confluence_signals.csv"
            shutil.copy(signal_file, dest)
            print(f"📁 Copied to MT4 directory: {dest}")
            
            print(f"\n📋 Confluence includes:")
            print(f"   • RSI Oversold")
            print(f"   • MACD Bullish Divergence")
            print(f"   • Support Level Bounce")
            print(f"   • All for {symbol}")
            
        except Exception as e:
            print(f"❌ Error creating confluence signals: {e}")
    
    def test_socket_connection(self):
        """Test socket connection"""
        print("\n🔌 Testing Socket Connection...")
        
        try:
            step = self.flow_tester.test_socket_communication()
            print(f"Result: {step.result.value}")
            print(f"Details: {step.details}")
            
        except Exception as e:
            print(f"❌ Socket test error: {e}")
    
    def test_csv_integrity(self):
        """Test CSV integrity"""
        print("\n📋 Testing CSV Integrity...")
        
        try:
            step = self.flow_tester.test_csv_integrity()
            print(f"Result: {step.result.value}")
            print(f"Details: {step.details}")
            
        except Exception as e:
            print(f"❌ CSV integrity test error: {e}")
    
    def run_end_to_end_test(self):
        """Run complete end-to-end test"""
        print("\n🎯 Running Complete End-to-End Test...")
        print("This will test the entire signal flow from source to MT4")
        
        confirm = input("Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            return
        
        try:
            summary = self.flow_tester.run_comprehensive_test()
            
            # Display results
            print(f"\n📊 Test Summary:")
            print(f"   Duration: {summary['duration_seconds']:.1f} seconds")
            print(f"   Passed: {summary['passed']}/{summary['total_steps']}")
            print(f"   Failed: {summary['failed']}/{summary['total_steps']}")
            
            if summary['failed'] == 0:
                print("✅ All tests passed - Signal system is working correctly!")
            else:
                print("❌ Some tests failed - Check individual results above")
            
        except Exception as e:
            print(f"❌ End-to-end test error: {e}")
    
    def view_system_status(self):
        """View current system status"""
        print("\n📊 SYSTEM STATUS")
        print("-" * 40)
        
        # Check MT4 connection
        health_file = self.eafix_dir / "health_metrics.csv"
        if health_file.exists():
            try:
                import csv
                with open(health_file, 'r') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    
                if rows:
                    last_row = rows[-1]
                    print(f"✅ MT4 EA Status: Connected")
                    print(f"   Last Heartbeat: {last_row.get('last_heartbeat', 'N/A')}")
                    print(f"   Database Connected: {last_row.get('database_connected', 'N/A')}")
                    print(f"   Bridge Connected: {last_row.get('ea_bridge_connected', 'N/A')}")
                else:
                    print("⚠️  MT4 EA Status: No health data")
            except Exception as e:
                print(f"❌ Error reading health metrics: {e}")
        else:
            print("❌ MT4 EA Status: No health file found")
        
        # Check signal files
        signal_files = [
            "active_calendar_signals.csv",
            "reentry_decisions.csv", 
            "trade_results.csv"
        ]
        
        print(f"\n📁 Signal Files:")
        for file_name in signal_files:
            file_path = self.eafix_dir / file_name
            if file_path.exists():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                print(f"   ✅ {file_name}: Last modified {mtime}")
            else:
                print(f"   ❌ {file_name}: Not found")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning Up Test Data...")
        
        confirm = input("This will delete all test files. Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            return
        
        try:
            # Clean test data directory
            if self.test_data_dir.exists():
                import shutil
                shutil.rmtree(self.test_data_dir)
                self.test_data_dir.mkdir()
                print(f"✅ Cleaned: {self.test_data_dir}")
            
            # Clean test files from MT4 directory
            test_patterns = ["*test*", "*manual*
