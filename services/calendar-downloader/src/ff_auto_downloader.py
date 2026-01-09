#!/usr/bin/env python3
# DOC_ID: DOC-SERVICE-0026
"""
Automated ForexFactory Calendar Downloader & Processor
Fully automated solution that:
1. Downloads ForexFactory CSV without user interaction
2. Processes through your existing Economic Calendar System pipeline
3. Generates anticipation events and equity market events
4. Outputs ready-to-trade CSV for MT4 integration
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import logging
from typing import List, Dict, Optional
import hashlib
import json

# Web automation imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium not available. Install with: pip install selenium webdriver-manager")

# Configuration
class Config:
    """Configuration for automated calendar processing"""
    
    # ForexFactory URL
    FOREXFACTORY_URL = "https://www.forexfactory.com/calendar"
    
    # Paths
    DOWNLOADS_PATH = Path.home() / "Downloads"
    OUTPUT_PATH = Path("./processed_calendar")
    ARCHIVE_PATH = Path("./calendar_archive")
    
    # File patterns (matching your existing system)
    CSV_PATTERNS = [
        "ff_calendar*.csv",
        "*calendar*thisweek*.csv", 
        "*economic*calendar*.csv",
        "*calendar*.csv"
    ]
    
    # Processing settings
    ANTICIPATION_HOURS = [1, 2, 4]  # Hours before events to create anticipation
    MAX_ANTICIPATION_EVENTS = 3     # Max anticipation events per original event
    
    # Market opening times (CST) - matching your system
    EQUITY_MARKET_OPENS = {
        "Tokyo": {"time": "21:00", "pairs": ["USDJPY", "AUDJPY", "EURJPY"]},
        "London": {"time": "02:00", "pairs": ["EURUSD", "GBPUSD", "EURGBP"]},
        "New York": {"time": "08:30", "pairs": ["EURUSD", "GBPUSD", "USDJPY", "USDCAD"]}
    }
    
    # Impact filtering (matching your system)
    VALID_IMPACTS = ["High", "Medium"]  # Only High (Red) and Medium (Orange)
    EXCLUDED_COUNTRIES = ["CHF"]        # Exclude Switzerland
    
    # Weekend filtering
    WEEKEND_BLOCK_START = {"day": 4, "hour": 15}  # Friday 15:00 CST
    WEEKEND_BLOCK_END = {"day": 6, "hour": 18}    # Sunday 18:00 CST

class AutomatedDownloader:
    """Automated ForexFactory CSV downloader using Selenium"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = self._setup_logging()
        self.download_dir = str(config.DOWNLOADS_PATH)
        
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('calendar_downloader.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def _setup_chrome_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver with download preferences"""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium not available. Install with: pip install selenium webdriver-manager")
        
        chrome_options = Options()
        
        # Download preferences
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Additional options for automation
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Optional: Run headless for server deployment
        # chrome_options.add_argument("--headless")
        
        # Setup driver with auto-download of ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to hide automation
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def download_calendar_csv(self) -> Optional[Path]:
        """Download ForexFactory calendar CSV automatically"""
        self.logger.info("Starting automated ForexFactory CSV download...")
        
        driver = None
        try:
            # Setup driver
            driver = self._setup_chrome_driver()
            
            # Get initial file list to detect new download
            initial_files = set(self.config.DOWNLOADS_PATH.glob("*.csv"))
            
            # Navigate to ForexFactory calendar
            self.logger.info(f"Navigating to {self.config.FOREXFACTORY_URL}")
            driver.get(self.config.FOREXFACTORY_URL)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "calendar"))
            )
            
            # Find and click CSV export button
            # ForexFactory typically has a CSV export option in the calendar header
            csv_selectors = [
                "a[href*='csv']",
                "button[data-export='csv']", 
                ".export-csv",
                "a[title*='CSV']",
                "a[title*='csv']",
                ".csv-export",
                "a:contains('CSV')",  # jQuery-style selector
            ]
            
            csv_button = None
            for selector in csv_selectors:
                try:
                    if "contains" in selector:
                        # Handle text-based search
                        elements = driver.find_elements(By.TAG_NAME, "a")
                        for element in elements:
                            if "csv" in element.text.lower():
                                csv_button = element
                                break
                    else:
                        csv_button = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if csv_button:
                        break
                except:
                    continue
            
            if not csv_button:
                # Try to find export/download section
                self.logger.warning("CSV button not found with standard selectors, trying alternative methods...")
                
                # Look for any download/export text
                elements = driver.find_elements(By.TAG_NAME, "a")
                for element in elements:
                    text = element.text.lower()
                    if any(word in text for word in ["csv", "export", "download"]):
                        csv_button = element
                        break
            
            if not csv_button:
                self.logger.error("Could not find CSV download button")
                return None
            
            # Click the CSV download button
            self.logger.info("Clicking CSV download button...")
            driver.execute_script("arguments[0].click();", csv_button)
            
            # Wait for download to complete
            self.logger.info("Waiting for download to complete...")
            download_timeout = 30  # 30 seconds timeout
            start_time = time.time()
            
            while time.time() - start_time < download_timeout:
                current_files = set(self.config.DOWNLOADS_PATH.glob("*.csv"))
                new_files = current_files - initial_files
                
                if new_files:
                    # Check if download is complete (no .crdownload files)
                    temp_files = list(self.config.DOWNLOADS_PATH.glob("*.crdownload"))
                    if not temp_files:
                        downloaded_file = max(new_files, key=lambda f: f.stat().st_mtime)
                        self.logger.info(f"Download completed: {downloaded_file}")
                        return downloaded_file
                
                time.sleep(1)
            
            self.logger.error("Download timeout reached")
            return None
            
        except Exception as e:
            self.logger.error(f"Error during download: {e}")
            return None
            
        finally:
            if driver:
                driver.quit()

class CalendarProcessor:
    """Process ForexFactory CSV through your existing pipeline logic"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def load_and_validate_csv(self, file_path: Path) -> pd.DataFrame:
        """Load and validate ForexFactory CSV"""
        try:
            # Read CSV - ForexFactory format
            df = pd.read_csv(file_path)
            
            # Validate expected columns (matching your CSV format)
            expected_cols = ['Title', 'Country', 'Date', 'Time', 'Impact', 'Forecast', 'Previous', 'URL']
            missing_cols = [col for col in expected_cols if col not in df.columns]
            
            if missing_cols:
                self.logger.warning(f"Missing columns: {missing_cols}")
            
            self.logger.info(f"Loaded {len(df)} events from {file_path}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading CSV: {e}")
            raise
    
    def filter_events(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter events according to your system rules"""
        original_count = len(df)
        
        # Remove low impact and excluded countries (matching your system)
        df = df[df['Impact'].isin(self.config.VALID_IMPACTS)]
        df = df[~df['Country'].isin(self.config.EXCLUDED_COUNTRIES)]
        
        # Remove rows with missing critical data
        df = df.dropna(subset=['Title', 'Country', 'Date', 'Time', 'Impact'])
        
        # Convert Date and Time to datetime for filtering
        df['EventDateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')
        df = df.dropna(subset=['EventDateTime'])
        
        # Remove weekend events (matching your weekend blocking logic)
        df = df[df['EventDateTime'].dt.dayofweek < 5]  # Monday to Friday only
        
        # Remove Friday after 15:00 CST and Sunday before 18:00 CST
        friday_filter = ~((df['EventDateTime'].dt.dayofweek == 4) & 
                         (df['EventDateTime'].dt.hour >= self.config.WEEKEND_BLOCK_START["hour"]))
        sunday_filter = ~((df['EventDateTime'].dt.dayofweek == 6) & 
                         (df['EventDateTime'].dt.hour < self.config.WEEKEND_BLOCK_END["hour"]))
        
        df = df[friday_filter & sunday_filter]
        
        filtered_count = len(df)
        self.logger.info(f"Filtered {original_count} → {filtered_count} events")
        
        return df.reset_index(drop=True)
    
    def create_anticipation_events(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create anticipation events before major announcements"""
        anticipation_events = []
        
        for _, event in df.iterrows():
            # Only create anticipation for High impact events
            if event['Impact'] != 'High':
                continue
                
            event_time = event['EventDateTime']
            
            # Create anticipation events at specified hours before
            for hours_before in self.config.ANTICIPATION_HOURS:
                if len(anticipation_events) >= self.config.MAX_ANTICIPATION_EVENTS * len(df):
                    break
                    
                anticipation_time = event_time - timedelta(hours=hours_before)
                
                # Skip if anticipation time is in the past
                if anticipation_time < datetime.now():
                    continue
                
                # Create anticipation event (matching your naming convention)
                anticipation_event = {
                    'Title': f"{hours_before}H Before {event['Title']} Anticipation",
                    'Country': event['Country'],
                    'Date': anticipation_time.strftime('%m-%d-%Y'),
                    'Time': anticipation_time.strftime('%I:%M%p'),
                    'Impact': event['Impact'],  # Keep original impact
                    'Forecast': 'Anticipation',
                    'Previous': 'Anticipation', 
                    'URL': event['URL'],
                    'EventDateTime': anticipation_time,
                    'EventType': 'ANTICIPATION',
                    'OriginalEvent': event['Title']
                }
                
                anticipation_events.append(anticipation_event)
        
        if anticipation_events:
            anticipation_df = pd.DataFrame(anticipation_events)
            self.logger.info(f"Created {len(anticipation_df)} anticipation events")
            return anticipation_df
        else:
            return pd.DataFrame()
    
    def create_equity_market_events(self) -> pd.DataFrame:
        """Create equity market opening events"""
        equity_events = []
        
        # Get current week's dates
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        
        for i in range(5):  # Monday to Friday
            day = start_of_week + timedelta(days=i)
            
            if day < today:  # Skip past days
                continue
                
            for market_name, market_info in self.config.EQUITY_MARKET_OPENS.items():
                market_time = datetime.strptime(f"{day.strftime('%Y-%m-%d')} {market_info['time']}", 
                                              '%Y-%m-%d %H:%M')
                
                # Create event for primary currency pair
                primary_pair = market_info['pairs'][0] if market_info['pairs'] else 'EURUSD'
                country = primary_pair[:3]  # First 3 letters as country code
                
                equity_event = {
                    'Title': f"{market_name} Market Open",
                    'Country': country,
                    'Date': market_time.strftime('%m-%d-%Y'),
                    'Time': market_time.strftime('%I:%M%p'),
                    'Impact': 'Medium',  # Market opens are Medium impact
                    'Forecast': 'Market Open',
                    'Previous': 'Market Open',
                    'URL': '',
                    'EventDateTime': market_time,
                    'EventType': 'EQUITY_OPEN',
                    'MarketName': market_name,
                    'TradingPairs': market_info['pairs']
                }
                
                equity_events.append(equity_event)
        
        if equity_events:
            equity_df = pd.DataFrame(equity_events)
            self.logger.info(f"Created {len(equity_df)} equity market events")
            return equity_df
        else:
            return pd.DataFrame()
    
    def create_strategy_ids(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create strategy IDs using your RCI system"""
        
        # Regional mapping (matching your system)
        region_map = {
            'USD': 1, 'CAD': 1,  # North America
            'EUR': 2, 'GBP': 2,  # Europe  
            'JPY': 3, 'AUD': 3, 'NZD': 3,  # Asia-Pacific
            'BRL': 4,  # Latin America
            'ZAR': 5, 'TRY': 5  # Middle East/Africa
        }
        
        # Country codes within regions
        country_codes = {
            'USD': '01', 'CAD': '02',
            'EUR': '11', 'GBP': '12', 
            'JPY': '21', 'AUD': '22', 'NZD': '23',
            'BRL': '31',
            'ZAR': '41', 'TRY': '42'
        }
        
        # Impact codes
        impact_codes = {'Medium': '1', 'High': '2'}
        
        def generate_strategy_id(country, impact):
            region = region_map.get(country, 9)  # Default to 9 for "Other"
            country_code = country_codes.get(country, '99')  # Default to 99
            impact_code = impact_codes.get(impact, '1')  # Default to Medium
            
            return f"{region}{country_code}{impact_code}"
        
        df['StrategyID'] = df.apply(lambda row: generate_strategy_id(row['Country'], row['Impact']), axis=1)
        
        return df
    
    def process_complete_calendar(self, raw_file: Path) -> pd.DataFrame:
        """Complete processing pipeline"""
        self.logger.info("Starting complete calendar processing...")
        
        # Load and filter original events
        df = self.load_and_validate_csv(raw_file)
        df = self.filter_events(df)
        
        # Create anticipation events
        anticipation_df = self.create_anticipation_events(df)
        
        # Create equity market events
        equity_df = self.create_equity_market_events()
        
        # Combine all events
        all_events = []
        
        # Add original events
        df['EventType'] = 'ECONOMIC'
        all_events.append(df)
        
        # Add anticipation events
        if not anticipation_df.empty:
            all_events.append(anticipation_df)
        
        # Add equity events
        if not equity_df.empty:
            all_events.append(equity_df)
        
        # Combine and sort chronologically
        if len(all_events) > 1:
            combined_df = pd.concat(all_events, ignore_index=True)
        else:
            combined_df = all_events[0]
        
        # Sort by event time
        combined_df = combined_df.sort_values('EventDateTime').reset_index(drop=True)
        
        # Generate strategy IDs
        combined_df = self.create_strategy_ids(combined_df)
        
        # Add processing metadata
        combined_df['ProcessedAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        combined_df['SourceFile'] = raw_file.name
        
        self.logger.info(f"Processing complete: {len(combined_df)} total events")
        
        return combined_df
    
    def export_for_mt4(self, df: pd.DataFrame, output_path: Path) -> Path:
        """Export processed calendar in MT4-compatible format"""
        
        # Create MT4-compatible columns (matching your EA format)
        mt4_df = pd.DataFrame()
        
        # Generate unique IDs
        mt4_df['id'] = df['EventDateTime'].dt.strftime('%Y%m%d%H%M') + '_' + df['Country']
        
        # Trading symbols (simplified - your system may have more complex mapping)
        mt4_df['symbol'] = df['Country'] + 'USD'
        
        # Event details
        mt4_df['eventName'] = df['Title']
        mt4_df['eventType'] = df.get('EventType', 'ECONOMIC')
        mt4_df['impact'] = df['Impact']
        mt4_df['tradeEnabled'] = 'true'
        
        # Timing
        mt4_df['entryTimeStr'] = df['EventDateTime'].dt.strftime('%Y.%m.%d %H:%M')
        mt4_df['offset'] = 0  # Your system uses -3 minutes default
        mt4_df['entryType'] = 'Event'
        
        # Trading parameters (matching your parameter sets)
        mt4_df['slPips'] = 20  # Default stop loss
        mt4_df['tpPips'] = 40  # Default take profit
        mt4_df['bufferPips'] = 10  # Default entry distance
        
        # Risk management
        mt4_df['trailingType'] = 'step'
        mt4_df['lotInput'] = 'AUTO'
        
        # Execution windows
        mt4_df['winStartStr'] = (df['EventDateTime'] - timedelta(minutes=5)).dt.strftime('%Y.%m.%d %H:%M')
        mt4_df['winEndStr'] = (df['EventDateTime'] + timedelta(minutes=5)).dt.strftime('%Y.%m.%d %H:%M')
        
        # Metadata
        mt4_df['rawEventTime'] = mt4_df['entryTimeStr']
        mt4_df['magicNumber'] = 0
        mt4_df['strategy'] = 'calendar'
        mt4_df['notes'] = df['Title']
        mt4_df['genTimestamp'] = datetime.now().strftime('%Y.%m.%d %H:%M')
        mt4_df['strategyId'] = df.get('StrategyID', '10101')
        
        # Export with semicolon separator (MT4 standard)
        output_file = output_path / f"processed_calendar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        mt4_df.to_csv(output_file, index=False, sep=';')
        
        self.logger.info(f"MT4 calendar exported to: {output_file}")
        return output_file

class AutomatedCalendarSystem:
    """Main automated calendar system orchestrator"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.downloader = AutomatedDownloader(self.config)
        self.processor = CalendarProcessor(self.config)
        self.logger = logging.getLogger(__name__)
        
        # Ensure output directories exist
        self.config.OUTPUT_PATH.mkdir(exist_ok=True)
        self.config.ARCHIVE_PATH.mkdir(exist_ok=True)
    
    def run_automated_process(self) -> Optional[Path]:
        """Run the complete automated process"""
        self.logger.info("=== Starting Automated ForexFactory Calendar Process ===")
        
        try:
            # Step 1: Download latest calendar
            downloaded_file = self.downloader.download_calendar_csv()
            if not downloaded_file:
                self.logger.error("Failed to download calendar CSV")
                return None
            
            # Step 2: Process through pipeline
            processed_df = self.processor.process_complete_calendar(downloaded_file)
            
            # Step 3: Export for MT4
            output_file = self.processor.export_for_mt4(processed_df, self.config.OUTPUT_PATH)
            
            # Step 4: Archive original file
            archive_file = self.config.ARCHIVE_PATH / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{downloaded_file.name}"
            downloaded_file.rename(archive_file)
            self.logger.info(f"Original file archived to: {archive_file}")
            
            self.logger.info("=== Automated Process Completed Successfully ===")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Automated process failed: {e}")
            return None
    
    def schedule_daily_run(self):
        """Schedule daily automated runs (integrate with your Sunday 12 PM schedule)"""
        import schedule
        
        # Schedule for Sunday 12 PM (matching your existing system)
        schedule.every().sunday.at("12:00").do(self.run_automated_process)
        
        # Optional: Add retry schedule every hour for 24 hours if Sunday run fails
        # This would need more sophisticated state management
        
        self.logger.info("Automated calendar system scheduled for Sunday 12:00 PM")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated ForexFactory Calendar Processor")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    parser.add_argument("--schedule", action="store_true", help="Run on schedule (Sunday 12 PM)")
    parser.add_argument("--output-dir", type=str, help="Custom output directory")
    
    args = parser.parse_args()
    
    # Setup configuration
    config = Config()
    if args.output_dir:
        config.OUTPUT_PATH = Path(args.output_dir)
    
    # Initialize system
    calendar_system = AutomatedCalendarSystem(config)
    
    if args.run_once:
        # Run once and exit
        result = calendar_system.run_automated_process()
        if result:
            print(f"Success! Processed calendar saved to: {result}")
            sys.exit(0)
        else:
            print("Failed to process calendar")
            sys.exit(1)
    
    elif args.schedule:
        # Run on schedule
        try:
            calendar_system.schedule_daily_run()
        except KeyboardInterrupt:
            print("Scheduled runs stopped by user")
            sys.exit(0)
    
    else:
        # Default: run once
        result = calendar_system.run_automated_process()
        if result:
            print(f"Success! Processed calendar saved to: {result}")
        else:
            print("Failed to process calendar")

if __name__ == "__main__":
    main()
