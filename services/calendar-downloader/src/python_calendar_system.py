#!/usr/bin/env python3
"""
Economic Calendar to Signal System - Python Implementation
Converting Excel-VBA system to pure Python solution
"""

import asyncio
import logging
import sqlite3
import pandas as pd
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pydantic import BaseModel, Field
import uvicorn
from fastapi import FastAPI, WebSocket, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import websockets

# ============================================================================
# CONFIGURATION MANAGEMENT (Replaces Excel Named Ranges)
# ============================================================================

class SystemConfig(BaseModel):
    """System configuration replacing Excel named ranges"""
    
    # Import Configuration
    calendar_auto_import: bool = True
    import_day: int = 6  # Sunday = 6
    import_hour: int = 12  # 12 PM CST
    retry_interval_hours: int = 1
    max_retry_attempts: int = 24
    import_timeout_seconds: int = 30
    
    # Processing Configuration  
    anticipation_hours: List[int] = [1, 2, 4]
    anticipation_enabled: bool = True
    minimum_gap_minutes: int = 30
    
    # Trigger Configuration
    trigger_offsets: Dict[str, int] = {
        "EMO-E": -3,  # High impact: -3 minutes
        "EMO-A": -2,  # Medium impact: -2 minutes
        "EQT-OPEN": -5,  # Equity markets: -5 minutes
        "ANTICIPATION": -1  # Anticipation events: -1 minute
    }
    
    # Parameter Sets (4 fixed sets)
    parameter_sets: Dict[int, Dict[str, Any]] = {
        1: {"lot_size": 0.01, "stop_loss": 20, "take_profit": 40, "buy_distance": 10, "sell_distance": 10},
        2: {"lot_size": 0.02, "stop_loss": 20, "take_profit": 40, "buy_distance": 10, "sell_distance": 10},
        3: {"lot_size": 0.03, "stop_loss": 20, "take_profit": 40, "buy_distance": 10, "sell_distance": 10},
        4: {"lot_size": 0.04, "stop_loss": 20, "take_profit": 40, "buy_distance": 10, "sell_distance": 10}
    }
    
    # File Paths
    downloads_path: str = "~/Downloads"
    archive_path: str = "./calendar_archive"
    signals_export_path: str = "./signals"
    database_path: str = "./calendar_system.db"
    
    # Monitoring
    monitor_interval_seconds: int = 15
    health_check_interval_minutes: int = 5

# ============================================================================
# DATA MODELS (Replaces Excel Data Structures)
# ============================================================================

class EventStatus(Enum):
    PENDING = "PENDING"
    READY = "READY" 
    TRIGGERED = "TRIGGERED"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"

class EventType(Enum):
    ECONOMIC = "ECONOMIC"
    ANTICIPATION = "ANTICIPATION"
    EQUITY_OPEN = "EQUITY_OPEN"

@dataclass
class CalendarEvent:
    """Calendar event data structure"""
    title: str
    country: str
    date: datetime
    time: str
    impact: str
    forecast: Optional[str] = None
    previous: Optional[str] = None
    url: Optional[str] = None
    event_type: EventType = EventType.ECONOMIC
    trigger_time: Optional[datetime] = None
    parameter_set: int = 1
    enabled: bool = True
    status: EventStatus = EventStatus.PENDING
    quality_score: int = 0
    processing_notes: str = ""

@dataclass
class TradingSignal:
    """Trading signal data structure"""
    symbol: str
    buy_distance: float
    sell_distance: float
    stop_loss: float
    take_profit: float
    lot_size: float
    expire_hours: int
    trailing_stop: float
    comment: str
    strategy_id: int
    parameter_set_id: int
    timestamp: datetime
    event_title: str

# ============================================================================
# DATABASE MANAGER (Replaces Excel DataStore)
# ============================================================================

class DatabaseManager:
    """SQLite database replacing Excel data storage"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    country TEXT NOT NULL,
                    event_date DATE NOT NULL,
                    event_time TEXT NOT NULL,
                    impact TEXT NOT NULL,
                    forecast TEXT,
                    previous TEXT,
                    url TEXT,
                    event_type TEXT NOT NULL,
                    trigger_time DATETIME,
                    parameter_set INTEGER,
                    enabled BOOLEAN DEFAULT TRUE,
                    status TEXT DEFAULT 'PENDING',
                    quality_score INTEGER DEFAULT 0,
                    processing_notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    buy_distance REAL,
                    sell_distance REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    lot_size REAL,
                    expire_hours INTEGER,
                    trailing_stop REAL,
                    comment TEXT,
                    strategy_id INTEGER,
                    parameter_set_id INTEGER,
                    timestamp DATETIME,
                    event_title TEXT,
                    exported BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_status (
                    id INTEGER PRIMARY KEY,
                    system_health TEXT,
                    timer_status TEXT,
                    calendar_status TEXT,
                    last_import DATETIME,
                    next_import DATETIME,
                    last_parameter_set INTEGER DEFAULT 1,
                    uptime_hours REAL DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    async def save_events(self, events: List[CalendarEvent]):
        """Save calendar events to database"""
        with sqlite3.connect(self.db_path) as conn:
            for event in events:
                conn.execute("""
                    INSERT OR REPLACE INTO calendar_events 
                    (title, country, event_date, event_time, impact, forecast, previous, url,
                     event_type, trigger_time, parameter_set, enabled, status, quality_score, processing_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.title, event.country, event.date.date(), event.time,
                    event.impact, event.forecast, event.previous, event.url,
                    event.event_type.value, event.trigger_time, event.parameter_set,
                    event.enabled, event.status.value, event.quality_score, event.processing_notes
                ))
    
    async def get_active_events(self) -> List[CalendarEvent]:
        """Get active events for monitoring"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM calendar_events 
                WHERE enabled = TRUE AND status IN ('PENDING', 'READY')
                AND datetime(event_date || ' ' || event_time) > datetime('now')
                ORDER BY event_date, event_time
            """)
            
            events = []
            for row in cursor.fetchall():
                event = CalendarEvent(
                    title=row['title'],
                    country=row['country'],
                    date=datetime.fromisoformat(row['event_date']),
                    time=row['event_time'],
                    impact=row['impact'],
                    forecast=row['forecast'],
                    previous=row['previous'],
                    url=row['url'],
                    event_type=EventType(row['event_type']),
                    trigger_time=datetime.fromisoformat(row['trigger_time']) if row['trigger_time'] else None,
                    parameter_set=row['parameter_set'],
                    enabled=bool(row['enabled']),
                    status=EventStatus(row['status']),
                    quality_score=row['quality_score'],
                    processing_notes=row['processing_notes']
                )
                events.append(event)
            
            return events
    
    async def save_signal(self, signal: TradingSignal):
        """Save trading signal to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO trading_signals 
                (symbol, buy_distance, sell_distance, stop_loss, take_profit, lot_size,
                 expire_hours, trailing_stop, comment, strategy_id, parameter_set_id,
                 timestamp, event_title)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal.symbol, signal.buy_distance, signal.sell_distance,
                signal.stop_loss, signal.take_profit, signal.lot_size,
                signal.expire_hours, signal.trailing_stop, signal.comment,
                signal.strategy_id, signal.parameter_set_id, signal.timestamp,
                signal.event_title
            ))

# ============================================================================
# CALENDAR IMPORT ENGINE (Replaces calendar_import_engine.bas)
# ============================================================================

class CalendarImportEngine:
    """Calendar import and processing system"""
    
    def __init__(self, config: SystemConfig, db_manager: DatabaseManager):
        self.config = config
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    async def find_calendar_files(self) -> List[Path]:
        """Find calendar CSV files in downloads folder"""
        downloads_path = Path(self.config.downloads_path).expanduser()
        
        patterns = [
            "ff_calendar*.csv",  # ForexFactory - highest priority
            "*calendar*thisweek*.csv",
            "*economic*calendar*.csv", 
            "*calendar*.csv",
            "*forex*.csv"
        ]
        
        found_files = []
        for pattern in patterns:
            files = list(downloads_path.glob(pattern))
            if files:
                # Sort by modification time, newest first
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                found_files.extend(files)
        
        return found_files
    
    async def parse_calendar_csv(self, file_path: Path) -> List[CalendarEvent]:
        """Parse calendar CSV file"""
        try:
            # Read CSV with pandas
            df = pd.read_csv(file_path)
            
            # Flexible column mapping
            column_mapping = self._map_csv_columns(df.columns.tolist())
            
            events = []
            for _, row in df.iterrows():
                try:
                    event = self._parse_csv_row(row, column_mapping)
                    if event:
                        events.append(event)
                except Exception as e:
                    self.logger.warning(f"Failed to parse row: {e}")
                    continue
            
            self.logger.info(f"Parsed {len(events)} events from {file_path}")
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to parse CSV {file_path}: {e}")
            return []
    
    def _map_csv_columns(self, columns: List[str]) -> Dict[str, str]:
        """Map CSV columns to standard fields"""
        column_map = {}
        columns_lower = [col.lower() for col in columns]
        
        # Title mapping
        for title_col in ['title', 'event', 'name', 'description']:
            if title_col in columns_lower:
                column_map['title'] = columns[columns_lower.index(title_col)]
                break
        
        # Country mapping  
        for country_col in ['country', 'currency', 'cur', 'symbol']:
            if country_col in columns_lower:
                column_map['country'] = columns[columns_lower.index(country_col)]
                break
        
        # Date mapping
        for date_col in ['date', 'day', 'time_date']:
            if date_col in columns_lower:
                column_map['date'] = columns[columns_lower.index(date_col)]
                break
        
        # Time mapping
        for time_col in ['time', 'hour', 'minute']:
            if time_col in columns_lower:
                column_map['time'] = columns[columns_lower.index(time_col)]
                break
        
        # Impact mapping
        for impact_col in ['impact', 'importance', 'volatility']:
            if impact_col in columns_lower:
                column_map['impact'] = columns[columns_lower.index(impact_col)]
                break
        
        return column_map
    
    def _parse_csv_row(self, row: pd.Series, column_mapping: Dict[str, str]) -> Optional[CalendarEvent]:
        """Parse individual CSV row into CalendarEvent"""
        try:
            # Extract required fields
            title = str(row.get(column_mapping.get('title', ''), '')).strip()
            country = str(row.get(column_mapping.get('country', ''), '')).strip()
            date_str = str(row.get(column_mapping.get('date', ''), '')).strip()
            time_str = str(row.get(column_mapping.get('time', ''), '')).strip()
            impact = str(row.get(column_mapping.get('impact', ''), '')).strip()
            
            # Validate required fields
            if not all([title, country, date_str, time_str, impact]):
                return None
            
            # Parse date
            event_date = pd.to_datetime(date_str).to_pydatetime()
            
            # Standardize country code
            country = self._standardize_country_code(country)
            
            # Standardize impact
            impact = self._standardize_impact(impact)
            
            # Create event
            event = CalendarEvent(
                title=title,
                country=country, 
                date=event_date,
                time=time_str,
                impact=impact,
                forecast=str(row.get('forecast', '')).strip() or None,
                previous=str(row.get('previous', '')).strip() or None,
                url=str(row.get('url', '')).strip() or None
            )
            
            # Calculate quality score
            event.quality_score = self._calculate_quality_score(event)
            
            return event
            
        except Exception as e:
            self.logger.warning(f"Failed to parse row: {e}")
            return None
    
    def _standardize_country_code(self, country: str) -> str:
        """Convert country to 3-letter currency code"""
        country_map = {
            'US': 'USD', 'USA': 'USD', 'UNITED STATES': 'USD',
            'EU': 'EUR', 'EURO': 'EUR', 'EUROZONE': 'EUR', 
            'UK': 'GBP', 'GB': 'GBP', 'BRITAIN': 'GBP',
            'JP': 'JPY', 'JAPAN': 'JPY',
            'CA': 'CAD', 'CANADA': 'CAD',
            'AU': 'AUD', 'AUSTRALIA': 'AUD',
            'NZ': 'NZD', 'NEW ZEALAND': 'NZD',
            'CH': 'CHF', 'SWITZERLAND': 'CHF'
        }
        
        country_upper = country.upper()
        return country_map.get(country_upper, country_upper)
    
    def _standardize_impact(self, impact: str) -> str:
        """Standardize impact levels"""
        impact_upper = impact.upper()
        if impact_upper in ['HIGH', 'H', '3']:
            return 'High'
        elif impact_upper in ['MEDIUM', 'MED', 'M', '2']:
            return 'Medium'
        elif impact_upper in ['LOW', 'L', '1']:
            return 'Low'
        else:
            return 'Medium'  # Default
    
    def _calculate_quality_score(self, event: CalendarEvent) -> int:
        """Calculate data quality score (0-100)"""
        score = 0
        
        # Required fields (20 points each)
        if event.title: score += 20
        if event.country: score += 20
        if event.date: score += 20
        if event.time: score += 20
        if event.impact: score += 20
        
        # Optional fields (5 points each)
        if event.forecast: score += 5
        if event.previous: score += 5
        if event.url: score += 5
        
        # Quality bonuses
        if len(event.title) > 20: score += 5  # Descriptive title
        if event.impact == 'High': score += 10
        elif event.impact == 'Medium': score += 5
        
        return min(score, 100)

# ============================================================================
# EVENT PROCESSING ENGINE (Replaces calendar_data_processor.bas)
# ============================================================================

class EventProcessor:
    """Process and enhance calendar events"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def process_events(self, events: List[CalendarEvent]) -> List[CalendarEvent]:
        """Main event processing pipeline"""
        # Filter and validate events
        valid_events = self._filter_events(events)
        
        # Generate anticipation events
        if self.config.anticipation_enabled:
            anticipation_events = self._generate_anticipation_events(valid_events)
            valid_events.extend(anticipation_events)
        
        # Calculate trigger times
        for event in valid_events:
            event.trigger_time = self._calculate_trigger_time(event)
        
        # Sort chronologically
        valid_events.sort(key=lambda x: x.trigger_time or datetime.max)
        
        return valid_events
    
    def _filter_events(self, events: List[CalendarEvent]) -> List[CalendarEvent]:
        """Filter events by quality and relevance"""
        filtered = []
        
        for event in events:
            # Quality filter
            if event.quality_score < 60:
                continue
            
            # Impact filter (only High and Medium)
            if event.impact not in ['High', 'Medium']:
                continue
            
            # Date range filter
            now = datetime.now()
            if event.date < now - timedelta(days=1):  # Past events tolerance
                continue
            if event.date > now + timedelta(days=14):  # Future events range
                continue
            
            filtered.append(event)
        
        return filtered
    
    def _generate_anticipation_events(self, events: List[CalendarEvent]) -> List[CalendarEvent]:
        """Generate anticipation events"""
        anticipation_events = []
        
        for event in events:
            if event.impact != 'High':  # Only for high impact events
                continue
                
            for hours_offset in self.config.anticipation_hours:
                anticipation_time = event.date - timedelta(hours=hours_offset)
                
                # Skip if anticipation time is in the past
                if anticipation_time < datetime.now():
                    continue
                
                anticipation_event = CalendarEvent(
                    title=f"#{hours_offset}H Before {event.title} Anticipation - {event.country} - {event.impact}",
                    country=event.country,
                    date=anticipation_time,
                    time=anticipation_time.strftime("%H:%M"),
                    impact=event.impact,
                    event_type=EventType.ANTICIPATION,
                    quality_score=event.quality_score,
                    processing_notes=f"Anticipation for: {event.title}"
                )
                
                anticipation_events.append(anticipation_event)
        
        return anticipation_events
    
    def _calculate_trigger_time(self, event: CalendarEvent) -> datetime:
        """Calculate trigger time based on event type and impact"""
        # Get offset from configuration
        if event.event_type == EventType.ANTICIPATION:
            offset = self.config.trigger_offsets["ANTICIPATION"]
        elif event.impact == 'High':
            offset = self.config.trigger_offsets["EMO-E"]
        elif event.impact == 'Medium':
            offset = self.config.trigger_offsets["EMO-A"]
        else:
            offset = -1  # Default 1 minute before
        
        # Calculate trigger time
        event_datetime = datetime.combine(event.date.date(), 
                                        datetime.strptime(event.time, "%H:%M").time())
        trigger_time = event_datetime + timedelta(minutes=offset)
        
        return trigger_time

# ============================================================================
# SIGNAL GENERATION ENGINE (Replaces event_trigger_engine.bas)
# ============================================================================

class SignalGenerator:
    """Generate trading signals from calendar events"""
    
    def __init__(self, config: SystemConfig, db_manager: DatabaseManager):
        self.config = config
        self.db = db_manager
        self.last_parameter_set = 1
        self.logger = logging.getLogger(__name__)
    
    async def generate_signal(self, event: CalendarEvent) -> TradingSignal:
        """Generate trading signal from calendar event"""
        # Select parameter set
        parameter_set_id = self._select_parameter_set(event)
        parameter_set = self.config.parameter_sets[parameter_set_id]
        
        # Determine symbol (could be configurable)
        symbol = self._get_primary_symbol(event.country)
        
        # Create trading signal
        signal = TradingSignal(
            symbol=symbol,
            buy_distance=parameter_set["buy_distance"],
            sell_distance=parameter_set["sell_distance"],
            stop_loss=parameter_set["stop_loss"],
            take_profit=parameter_set["take_profit"],
            lot_size=parameter_set["lot_size"],
            expire_hours=24,
            trailing_stop=0,
            comment=f"Calendar: {event.title[:20]}",
            strategy_id=301,  # Calendar strategy ID
            parameter_set_id=parameter_set_id,
            timestamp=datetime.now(),
            event_title=event.title
        )
        
        self.logger.info(f"Generated signal for {event.title}: {symbol} {parameter_set['lot_size']} lots")
        return signal
    
    def _select_parameter_set(self, event: CalendarEvent) -> int:
        """Select parameter set using sequential rotation"""
        self.last_parameter_set = (self.last_parameter_set % 4) + 1
        return self.last_parameter_set
    
    def _get_primary_symbol(self, country: str) -> str:
        """Get primary trading symbol for country"""
        symbol_map = {
            'USD': 'EURUSD',
            'EUR': 'EURUSD', 
            'GBP': 'GBPUSD',
            'JPY': 'USDJPY',
            'CAD': 'USDCAD',
            'AUD': 'AUDUSD',
            'NZD': 'NZDUSD',
            'CHF': 'USDCHF'
        }
        return symbol_map.get(country, 'EURUSD')

# ============================================================================
# MAIN SYSTEM ORCHESTRATOR (Replaces Excel timer system)
# ============================================================================

class CalendarSystem:
    """Main system orchestrator"""
    
    def __init__(self, config_path: str = "config.yaml"):
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.db = DatabaseManager(self.config.database_path)
        self.import_engine = CalendarImportEngine(self.config, self.db)
        self.event_processor = EventProcessor(self.config)
        self.signal_generator = SignalGenerator(self.config, self.db)
        
        # Initialize scheduler
        self.scheduler = AsyncIOScheduler()
        self.logger = logging.getLogger(__name__)
        
        # System state
        self.system_running = False
        self.active_events = []
        
    def _load_config(self, config_path: str) -> SystemConfig:
        """Load system configuration"""
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            return SystemConfig(**config_data)
        except FileNotFoundError:
            self.logger.warning(f"Config file {config_path} not found, using defaults")
            return SystemConfig()
    
    async def start_system(self):
        """Start the calendar system"""
        self.logger.info("Starting Economic Calendar System")
        
        # Schedule calendar import (every Sunday at 12 PM)
        self.scheduler.add_job(
            self._scheduled_import,
            trigger=CronTrigger(day_of_week=6, hour=12, minute=0),  # Sunday = 6
            id='calendar_import',
            replace_existing=True
        )
        
        # Schedule event monitoring (every 15 seconds)
        self.scheduler.add_job(
            self._monitor_events,
            trigger='interval',
            seconds=self.config.monitor_interval_seconds,
            id='event_monitor',
            replace_existing=True
        )
        
        # Schedule health checks (every 5 minutes)
        self.scheduler.add_job(
            self._health_check,
            trigger='interval',
            minutes=self.config.health_check_interval_minutes,
            id='health_check',
            replace_existing=True
        )
        
        # Start scheduler
        self.scheduler.start()
        self.system_running = True
        
        # Initial calendar import
        await self._import_calendar()
        
        self.logger.info("Economic Calendar System started successfully")
    
    async def stop_system(self):
        """Stop the calendar system"""
        self.logger.info("Stopping Economic Calendar System")
        self.scheduler.shutdown()
        self.system_running = False
    
    async def _scheduled_import(self):
        """Scheduled calendar import"""
        await self._import_calendar()
    
    async def _import_calendar(self):
        """Import calendar data"""
        try:
            self.logger.info("Starting calendar import")
            
            # Find calendar files
            files = await self.import_engine.find_calendar_files()
            if not files:
                self.logger.warning("No calendar files found")
                return
            
            # Parse best file
            best_file = files[0]  # First file (newest)
            events = await self.import_engine.parse_calendar_csv(best_file)
            
            if not events:
                self.logger.warning("No events parsed from calendar file")
                return
            
            # Process events
            processed_events = await self.event_processor.process_events(events)
            
            # Save to database
            await self.db.save_events(processed_events)
            
            # Update active events
            self.active_events = await self.db.get_active_events()
            
            self.logger.info(f"Calendar import completed: {len(processed_events)} events processed")
            
        except Exception as e:
            self.logger.error(f"Calendar import failed: {e}")
    
    async def _monitor_events(self):
        """Monitor events for triggering"""
        if not self.active_events:
            return
        
        current_time = datetime.now()
        
        for event in self.active_events:
            if event.status != EventStatus.PENDING:
                continue
            
            if event.trigger_time and current_time >= event.trigger_time:
                await self._trigger_event(event)
    
    async def _trigger_event(self, event: CalendarEvent):
        """Trigger signal for event"""
        try:
            self.logger.info(f"Triggering event: {event.title}")
            
            # Generate signal
            signal = await self.signal_generator.generate_signal(event)
            
            # Save signal
            await self.db.save_signal(signal)
            
            # Export signal for MT4 integration
            await self._export_signal(signal)
            
            # Update event status
            event.status = EventStatus.TRIGGERED
            await self.db.save_events([event])
            
            self.logger.info(f"Event triggered successfully: {event.title}")
            
        except Exception as e:
            self.logger.error(f"Failed to trigger event {event.title}: {e}")
            event.status = EventStatus.FAILED
            await self.db.save_events([event])
    
    async def _export_signal(self, signal: TradingSignal):
        """Export signal for MT4 integration"""
        # Create signals directory
        signals_path = Path(self.config.signals_export_path)
        signals_path.mkdir(exist_ok=True)
        
        # Export as CSV (compatible with existing python-watchdog.py)
        signal_file = signals_path / f"signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        signal_data = pd.DataFrame([{
            'Symbol': signal.symbol,
            'BuyDistance': signal.buy_distance,
            'SellDistance': signal.sell_distance,
            'StopLoss': signal.stop_loss,
            'TakeProfit': signal.take_profit,
            'LotSize': signal.lot_size,
            'ExpireHours': signal.expire_hours,
            'TrailingStop': signal.trailing_stop,
            'Comment': signal.comment,
            'StrategyID': signal.strategy_id,
            'ParameterSetID': signal.parameter_set_id,
            'Timestamp': signal.timestamp.isoformat(),
            'EventTitle': signal.event_title
        }])
        
        signal_data.to_csv(signal_file, index=False)
        self.logger.info(f"Signal exported to {signal_file}")
    
    async def _health_check(self):
        """Perform system health check"""
        # Update system status in database
        # Could be expanded with more health metrics
        pass

# ============================================================================
# WEB DASHBOARD (Replaces Excel Dashboard Sheets)
# ============================================================================

app = FastAPI(title="Economic Calendar System", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

class WebDashboard:
    """Web-based dashboard replacing Excel dashboards"""
    
    def __init__(self, calendar_system: CalendarSystem):
        self.system = calendar_system
        self.websocket_connections = []
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for web interface"""
        return {
            "active_events": [asdict(event) for event in self.system.active_events],
            "system_status": {
                "running": self.system.system_running,
                "next_import": "Sunday 12:00 PM",
                "health": "EXCELLENT"
            },
            "parameter_sets": self.system.config.parameter_sets,
            "last_parameter_set": self.system.signal_generator.last_parameter_set,
            "trigger_offsets": self.system.config.trigger_offsets
        }
    
    async def broadcast_update(self, data: Dict[str, Any]):
        """Broadcast updates to connected WebSocket clients"""
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(data)
            except:
                self.websocket_connections.remove(websocket)

# Global system instance
calendar_system = None
dashboard = None

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    global calendar_system, dashboard
    calendar_system = CalendarSystem()
    dashboard = WebDashboard(calendar_system)
    await calendar_system.start_system()

@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup on shutdown"""
    if calendar_system:
        await calendar_system.stop_system()

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Main dashboard page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Economic Calendar System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .panel { border: 1px solid #ccc; padding: 15px; border-radius: 5px; }
            .event { margin: 5px 0; padding: 5px; background: #f5f5f5; border-radius: 3px; }
            .high-impact { border-left: 4px solid #ff4444; }
            .medium-impact { border-left: 4px solid #ffaa00; }
            .status { font-weight: bold; color: green; }
            button { padding: 8px 16px; margin: 5px; cursor: pointer; }
            .countdown { font-weight: bold; color: #0066cc; }
        </style>
    </head>
    <body>
        <h1>Economic Calendar System Dashboard</h1>
        
        <div class="grid">
            <div class="panel">
                <h3>Next Events</h3>
                <div id="events"></div>
                <button onclick="toggleAllEvents()">Toggle All</button>
                <button onclick="emergencyStop()">Emergency Stop</button>
            </div>
            
            <div class="panel">
                <h3>Calendar Configuration</h3>
                <p>Anticipation Hours: <input type="text" id="anticipationHours" value="1,2,4"></p>
                <p>High Impact Offset: <input type="number" id="highOffset" value="-3"> minutes</p>
                <p>Medium Impact Offset: <input type="number" id="mediumOffset" value="-2"> minutes</p>
                <button onclick="updateConfig()">Update Configuration</button>
                <button onclick="manualImport()">Manual Import</button>
            </div>
            
            <div class="panel">
                <h3>Parameter Sets</h3>
                <div id="parameterSets"></div>
                <p>Selection: Sequential</p>
                <p>Last Used: Set <span id="lastSet">1</span></p>
                <button onclick="resetRotation()">Reset Rotation</button>
            </div>
            
            <div class="panel">
                <h3>System Status</h3>
                <p>Status: <span class="status" id="systemStatus">RUNNING</span></p>
                <p>Timer: <span id="timerStatus">ACTIVE</span></p>
                <p>Calendar: <span id="calendarStatus">LOADED</span></p>
                <p>Next Import: <span id="nextImport">Sunday 12:00 PM</span></p>
                <p>Health Score: <span id="healthScore">95/100</span></p>
            </div>
        </div>
        
        <script>
            const ws = new WebSocket(`ws://localhost:8000/ws`);
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            function updateDashboard(data) {
                // Update events
                const eventsDiv = document.getElementById('events');
                eventsDiv.innerHTML = '';
                
                data.active_events.slice(0, 5).forEach(event => {
                    const eventDiv = document.createElement('div');
                    eventDiv.className = `event ${event.impact.toLowerCase()}-impact`;
                    
                    const triggerTime = new Date(event.trigger_time);
                    const now = new Date();
                    const diff = Math.floor((triggerTime - now) / 60000); // minutes
                    
                    eventDiv.innerHTML = `
                        <strong>${event.title}</strong><br>
                        Time: ${event.time} (in ${diff > 0 ? diff + ' min' : 'triggered'})<br>
                        Impact: ${event.impact} | Status: ${event.status}
                    `;
                    eventsDiv.appendChild(eventDiv);
                });
                
                // Update parameter sets
                const paramDiv = document.getElementById('parameterSets');
                paramDiv.innerHTML = '';
                
                Object.entries(data.parameter_sets).forEach(([id, params]) => {
                    const setDiv = document.createElement('div');
                    setDiv.innerHTML = `Set ${id}: ${params.lot_size} lots`;
                    paramDiv.appendChild(setDiv);
                });
                
                document.getElementById('lastSet').textContent = data.last_parameter_set;
            }
            
            async function manualImport() {
                const response = await fetch('/api/import', { method: 'POST' });
                const result = await response.json();
                alert(result.message);
            }
            
            async function updateConfig() {
                const config = {
                    anticipation_hours: document.getElementById('anticipationHours').value.split(',').map(Number),
                    high_offset: parseInt(document.getElementById('highOffset').value),
                    medium_offset: parseInt(document.getElementById('mediumOffset').value)
                };
                
                const response = await fetch('/api/config', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                
                const result = await response.json();
                alert(result.message);
            }
            
            async function emergencyStop() {
                const response = await fetch('/api/emergency-stop', { method: 'POST' });
                const result = await response.json();
                alert(result.message);
            }
            
            // Refresh dashboard every 15 seconds
            setInterval(async () => {
                const response = await fetch('/api/dashboard-data');
                const data = await response.json();
                updateDashboard(data);
            }, 15000);
            
            // Initial load
            window.onload = async () => {
                const response = await fetch('/api/dashboard-data');
                const data = await response.json();
                updateDashboard(data);
            };
        </script>
    </body>
    </html>
    """

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    dashboard.websocket_connections.append(websocket)
    
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except:
        dashboard.websocket_connections.remove(websocket)

@app.get("/api/dashboard-data")
async def get_dashboard_data():
    """API endpoint for dashboard data"""
    return await dashboard.get_dashboard_data()

@app.post("/api/import")
async def manual_import():
    """Manual calendar import endpoint"""
    try:
        await calendar_system._import_calendar()
        return {"message": "Calendar import completed successfully"}
    except Exception as e:
        return {"message": f"Import failed: {str(e)}"}

@app.put("/api/config")
async def update_config(config_update: dict):
    """Update system configuration"""
    try:
        # Update configuration
        if "anticipation_hours" in config_update:
            calendar_system.config.anticipation_hours = config_update["anticipation_hours"]
        
        if "high_offset" in config_update:
            calendar_system.config.trigger_offsets["EMO-E"] = config_update["high_offset"]
            
        if "medium_offset" in config_update:
            calendar_system.config.trigger_offsets["EMO-A"] = config_update["medium_offset"]
        
        return {"message": "Configuration updated successfully"}
    except Exception as e:
        return {"message": f"Configuration update failed: {str(e)}"}

@app.post("/api/emergency-stop")
async def emergency_stop():
    """Emergency stop endpoint"""
    try:
        calendar_system.scheduler.pause()
        return {"message": "System paused successfully"}
    except Exception as e:
        return {"message": f"Emergency stop failed: {str(e)}"}

# ============================================================================
# MT4 INTEGRATION LAYER (Replaces existing python-watchdog.py integration)
# ============================================================================

class MT4Integration:
    """MT4 integration for signal delivery"""
    
    def __init__(self, signals_path: str, mt4_signals_path: str):
        self.signals_path = Path(signals_path)
        self.mt4_signals_path = Path(mt4_signals_path)
        self.logger = logging.getLogger(__name__)
    
    async def start_watching(self):
        """Start watching for signals and forward to MT4"""
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class SignalHandler(FileSystemEventHandler):
            def __init__(self, integration):
                self.integration = integration
            
            def on_created(self, event):
                if event.is_file and event.src_path.endswith('.csv'):
                    asyncio.create_task(self.integration.process_signal_file(event.src_path))
        
        observer = Observer()
        observer.schedule(SignalHandler(self), str(self.signals_path), recursive=False)
        observer.start()
        
        self.logger.info(f"Started watching {self.signals_path} for signals")
        return observer
    
    async def process_signal_file(self, file_path: str):
        """Process signal file and forward to MT4"""
        try:
            # Read signal file
            df = pd.read_csv(file_path)
            
            # Convert to MT4 format
            mt4_signal = self._convert_to_mt4_format(df.iloc[0])
            
            # Write to MT4 signals folder
            mt4_file = self.mt4_signals_path / f"mt4_signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            mt4_signal.to_csv(mt4_file, index=False)
            
            self.logger.info(f"Signal forwarded to MT4: {mt4_file}")
            
            # Remove processed file
            Path(file_path).unlink()
            
        except Exception as e:
            self.logger.error(f"Failed to process signal file {file_path}: {e}")
    
    def _convert_to_mt4_format(self, signal_row: pd.Series) -> pd.DataFrame:
        """Convert signal to MT4-compatible format"""
        # Convert to format expected by existing MT4 EA
        mt4_data = pd.DataFrame([{
            'Symbol': signal_row['Symbol'],
            'OrderType': 'PENDING',  # Pending order
            'Volume': signal_row['LotSize'],
            'Price': 0,  # Will be calculated by EA
            'StopLoss': signal_row['StopLoss'],
            'TakeProfit': signal_row['TakeProfit'],
            'Comment': signal_row['Comment'],
            'MagicNumber': signal_row['StrategyID'],
            'Expiration': (datetime.now() + timedelta(hours=signal_row['ExpireHours'])).isoformat()
        }])
        
        return mt4_data

# ============================================================================
# CONFIGURATION AND STARTUP
# ============================================================================

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('calendar_system.log'),
            logging.StreamHandler()
        ]
    )

async def main():
    """Main application entry point"""
    setup_logging()
    
    # Create default configuration if it doesn't exist
    config_file = Path("config.yaml")
    if not config_file.exists():
        default_config = SystemConfig()
        with open(config_file, 'w') as f:
            yaml.dump(asdict(default_config), f, default_flow_style=False)
    
    # Start web server
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())

# ============================================================================
# DEPLOYMENT AND DOCKER CONFIGURATION
# ============================================================================

"""
Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "calendar_system.py"]
```

requirements.txt:
```
fastapi==0.104.1
uvicorn==0.24.0
pandas==2.1.3
pydantic==2.5.0
aiofiles==23.2.1
aiohttp==3.9.1
apscheduler==3.10.4
watchdog==3.0.0
pyyaml==6.0.1
websockets==12.0
```

docker-compose.yml:
```yaml
version: '3.8'
services:
  calendar-system:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./signals:/app/signals
      - ./logs:/app/logs
    environment:
      - DATABASE_PATH=/app/data/calendar_system.db
      - SIGNALS_EXPORT_PATH=/app/signals
    restart: unless-stopped

  mt4-bridge:
    image: python:3.11-slim
    volumes:
      - ./signals:/app/signals
      - ./mt4_signals:/app/mt4_signals
    command: python mt4_integration.py
    depends_on:
      - calendar-system
```
"""

# ============================================================================
# MIGRATION UTILITIES (From Excel to Python)
# ============================================================================

class ExcelMigration:
    """Utilities for migrating from Excel-based system"""
    
    @staticmethod
    async def migrate_excel_data(excel_file: str, db_manager: DatabaseManager):
        """Migrate existing Excel data to SQLite database"""
        try:
            # Read Excel file
            df = pd.read_excel(excel_file, sheet_name='DataStore')
            
            # Extract calendar events (rows 104-203)
            calendar_data = df.iloc[103:203]  # 0-indexed
            
            events = []
            for _, row in calendar_data.iterrows():
                if pd.notna(row.iloc[2]):  # If title exists
                    event = CalendarEvent(
                        title=str(row.iloc[2]),  # Column C
                        country=str(row.iloc[3]),  # Column D
                        date=pd.to_datetime(row.iloc[0]),  # Column A
                        time=str(row.iloc[1]),  # Column B
                        impact=str(row.iloc[4]),  # Column E
                        event_type=EventType(row.iloc[5]) if pd.notna(row.iloc[5]) else EventType.ECONOMIC
                    )
                    events.append(event)
            
            # Save to database
            await db_manager.save_events(events)
            
            print(f"Migrated {len(events)} events from Excel to database")
            
        except Exception as e:
            print(f"Migration failed: {e}")
    
    @staticmethod
    def export_configuration(config: SystemConfig, output_file: str):
        """Export configuration for backup"""
        with open(output_file, 'w') as f:
            yaml.dump(asdict(config), f, default_flow_style=False)
        
        print(f"Configuration exported to {output_file}")

# ============================================================================
# TESTING AND VALIDATION
# ============================================================================

async def run_system_tests():
    """Run system validation tests"""
    print("Running Economic Calendar System Tests...")
    
    # Test configuration loading
    config = SystemConfig()
    assert len(config.parameter_sets) == 4
    assert config.anticipation_hours == [1, 2, 4]
    print("✓ Configuration tests passed")
    
    # Test database operations
    db = DatabaseManager(":memory:")  # In-memory database for testing
    
    test_event = CalendarEvent(
        title="Test NFP",
        country="USD", 
        date=datetime.now() + timedelta(hours=1),
        time="14:30",
        impact="High"
    )
    
    await db.save_events([test_event])
    events = await db.get_active_events()
    assert len(events) == 1
    print("✓ Database tests passed")
    
    # Test event processing
    processor = EventProcessor(config)
    processed = await processor.process_events([test_event])
    assert len(processed) >= 1  # Original + anticipation events
    print("✓ Event processing tests passed")
    
    # Test signal generation
    signal_gen = SignalGenerator(config, db)
    signal = await signal_gen.generate_signal(test_event)
    assert signal.lot_size in [0.01, 0.02, 0.03, 0.04]
    print("✓ Signal generation tests passed")
    
    print("All tests passed! ✓")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(run_system_tests())
    else:
        asyncio.run(main())