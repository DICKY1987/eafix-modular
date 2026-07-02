"""
Cost Tracking Integration
Integration with CLI Multi-Rapid platform cost tracking system
"""

import json
import time
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer
    PYQT_VERSION = 6
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSignal, QTimer
    PYQT_VERSION = 5

logger = logging.getLogger(__name__)


@dataclass
class CostEntry:
    """Individual cost tracking entry"""
    timestamp: float
    task_type: str
    service: str
    cost: float
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_cache_read: int = 0
    tokens_cache_write: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CostEntry':
        """Create from dictionary"""
        return cls(**data)


class CostTracker(QObject):
    """
    Cost tracking system with budget monitoring and platform integration
    """

    cost_updated = pyqtSignal(float)  # Current total cost
    budget_warning = pyqtSignal(str, float, float)  # Message, current, limit
    budget_exceeded = pyqtSignal(str, float, float)  # Message, current, limit

    def __init__(self, platform_url: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__()
        self.platform_url = platform_url
        self.api_key = api_key

        # Local storage
        self.cost_log_file = Path("cost_ledger.jsonl")
        self.cost_entries = []

        # Budget settings
        self.daily_budget = 50.0
        self.weekly_budget = 300.0
        self.monthly_budget = 1000.0
        self.warning_threshold = 0.8  # 80% of budget

        # Current usage
        self.daily_usage = 0.0
        self.weekly_usage = 0.0
        self.monthly_usage = 0.0

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.sync_with_platform)
        self.update_timer.start(60000)  # Sync every minute

        # Initialize
        self.load_cost_entries()
        self.calculate_current_usage()

    def load_cost_entries(self):
        """Load cost entries from local file"""
        if not self.cost_log_file.exists():
            return

        try:
            with open(self.cost_log_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        entry = CostEntry.from_dict(data)
                        self.cost_entries.append(entry)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid cost entry: {e}")

            logger.info(f"Loaded {len(self.cost_entries)} cost entries")

        except Exception as e:
            logger.error(f"Failed to load cost entries: {e}")

    def save_cost_entry(self, entry: CostEntry):
        """Save cost entry to local file"""
        try:
            # Append to JSONL file
            with open(self.cost_log_file, 'a') as f:
                f.write(json.dumps(entry.to_dict()) + '\n')

            # Add to memory
            self.cost_entries.append(entry)

            # Update usage calculations
            self.calculate_current_usage()

            logger.debug(f"Cost entry saved: {entry.service} ${entry.cost:.4f}")

        except Exception as e:
            logger.error(f"Failed to save cost entry: {e}")

    def record_command_cost(self, command: str, service: str, cost: float,
                          tokens_input: int = 0, tokens_output: int = 0):
        """Record cost for a command execution"""
        entry = CostEntry(
            timestamp=time.time(),
            task_type="command_execution",
            service=service,
            cost=cost,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            metadata={
                "command": command,
                "user_agent": "gui_terminal"
            }
        )

        self.save_cost_entry(entry)
        self.check_budget_limits()

    def record_ai_service_cost(self, task_type: str, service: str, cost: float,
                             tokens_input: int = 0, tokens_output: int = 0,
                             tokens_cache_read: int = 0, tokens_cache_write: int = 0,
                             metadata: Optional[Dict[str, Any]] = None):
        """Record cost for AI service usage"""
        entry = CostEntry(
            timestamp=time.time(),
            task_type=task_type,
            service=service,
            cost=cost,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_cache_read=tokens_cache_read,
            tokens_cache_write=tokens_cache_write,
            metadata=metadata or {}
        )

        self.save_cost_entry(entry)
        self.check_budget_limits()

    def calculate_current_usage(self):
        """Calculate current usage for different time periods"""
        now = time.time()
        day_seconds = 24 * 60 * 60
        week_seconds = 7 * day_seconds
        month_seconds = 30 * day_seconds

        # Reset usage
        self.daily_usage = 0.0
        self.weekly_usage = 0.0
        self.monthly_usage = 0.0

        # Calculate from entries
        for entry in self.cost_entries:
            age = now - entry.timestamp

            if age <= day_seconds:
                self.daily_usage += entry.cost
            if age <= week_seconds:
                self.weekly_usage += entry.cost
            if age <= month_seconds:
                self.monthly_usage += entry.cost

        # Emit signal
        self.cost_updated.emit(self.daily_usage)

    def check_budget_limits(self):
        """Check if budget limits are approached or exceeded"""
        # Daily budget check
        if self.daily_usage >= self.daily_budget:
            self.budget_exceeded.emit(
                "Daily budget exceeded!",
                self.daily_usage,
                self.daily_budget
            )
        elif self.daily_usage >= self.daily_budget * self.warning_threshold:
            self.budget_warning.emit(
                "Approaching daily budget limit",
                self.daily_usage,
                self.daily_budget
            )

        # Weekly budget check
        if self.weekly_usage >= self.weekly_budget:
            self.budget_exceeded.emit(
                "Weekly budget exceeded!",
                self.weekly_usage,
                self.weekly_budget
            )
        elif self.weekly_usage >= self.weekly_budget * self.warning_threshold:
            self.budget_warning.emit(
                "Approaching weekly budget limit",
                self.weekly_usage,
                self.weekly_budget
            )

        # Monthly budget check
        if self.monthly_usage >= self.monthly_budget:
            self.budget_exceeded.emit(
                "Monthly budget exceeded!",
                self.monthly_usage,
                self.monthly_budget
            )
        elif self.monthly_usage >= self.monthly_budget * self.warning_threshold:
            self.budget_warning.emit(
                "Approaching monthly budget limit",
                self.monthly_usage,
                self.monthly_budget
            )

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary"""
        return {
            "daily": {
                "usage": self.daily_usage,
                "budget": self.daily_budget,
                "percentage": (self.daily_usage / self.daily_budget) * 100 if self.daily_budget > 0 else 0
            },
            "weekly": {
                "usage": self.weekly_usage,
                "budget": self.weekly_budget,
                "percentage": (self.weekly_usage / self.weekly_budget) * 100 if self.weekly_budget > 0 else 0
            },
            "monthly": {
                "usage": self.monthly_usage,
                "budget": self.monthly_budget,
                "percentage": (self.monthly_usage / self.monthly_budget) * 100 if self.monthly_budget > 0 else 0
            },
            "total_entries": len(self.cost_entries)
        }

    def get_service_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get cost breakdown by service"""
        breakdown = {}

        for entry in self.cost_entries:
            service = entry.service
            if service not in breakdown:
                breakdown[service] = {
                    "total_cost": 0.0,
                    "entry_count": 0,
                    "total_tokens_input": 0,
                    "total_tokens_output": 0
                }

            breakdown[service]["total_cost"] += entry.cost
            breakdown[service]["entry_count"] += 1
            breakdown[service]["total_tokens_input"] += entry.tokens_input
            breakdown[service]["total_tokens_output"] += entry.tokens_output

        return breakdown

    def get_recent_entries(self, count: int = 20) -> List[Dict[str, Any]]:
        """Get recent cost entries"""
        recent = sorted(self.cost_entries, key=lambda x: x.timestamp, reverse=True)[:count]
        return [entry.to_dict() for entry in recent]

    def sync_with_platform(self):
        """Sync cost data with platform"""
        if not self.platform_url or not self.api_key:
            return

        try:
            # Get usage summary
            summary = self.get_usage_summary()

            # Send to platform
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "source": "gui_terminal",
                "timestamp": time.time(),
                "usage_summary": summary,
                "service_breakdown": self.get_service_breakdown()
            }

            response = requests.post(
                f"{self.platform_url}/cost-tracking/sync",
                json=data,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                logger.debug("Cost data synced with platform")
            else:
                logger.warning(f"Platform sync failed: {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Platform sync error: {e}")
        except Exception as e:
            logger.error(f"Unexpected sync error: {e}")

    def set_budget_limits(self, daily: float, weekly: float, monthly: float):
        """Set budget limits"""
        self.daily_budget = daily
        self.weekly_budget = weekly
        self.monthly_budget = monthly

        # Recheck after updating limits
        self.check_budget_limits()

        logger.info(f"Budget limits updated: Daily=${daily}, Weekly=${weekly}, Monthly=${monthly}")

    def export_cost_report(self, export_path: str, format: str = "json"):
        """Export cost report"""
        try:
            report_data = {
                "generated_at": datetime.utcnow().isoformat(),
                "summary": self.get_usage_summary(),
                "service_breakdown": self.get_service_breakdown(),
                "recent_entries": self.get_recent_entries(100)
            }

            export_file = Path(export_path)

            if format.lower() == "json":
                with open(export_file, 'w') as f:
                    json.dump(report_data, f, indent=2)
            elif format.lower() == "csv":
                import csv
                with open(export_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Timestamp', 'Service', 'Task Type', 'Cost', 'Tokens Input', 'Tokens Output'])

                    for entry in self.cost_entries:
                        writer.writerow([
                            datetime.fromtimestamp(entry.timestamp).isoformat(),
                            entry.service,
                            entry.task_type,
                            entry.cost,
                            entry.tokens_input,
                            entry.tokens_output
                        ])

            logger.info(f"Cost report exported to: {export_path}")

        except Exception as e:
            logger.error(f"Failed to export cost report: {e}")

    def reset_usage_data(self, confirm: bool = False):
        """Reset usage data (use with caution)"""
        if not confirm:
            raise ValueError("Reset requires confirmation")

        try:
            # Backup current data
            backup_file = self.cost_log_file.with_suffix('.backup.jsonl')
            if self.cost_log_file.exists():
                import shutil
                shutil.copy2(self.cost_log_file, backup_file)

            # Clear data
            self.cost_entries.clear()
            if self.cost_log_file.exists():
                self.cost_log_file.unlink()

            # Reset usage
            self.daily_usage = 0.0
            self.weekly_usage = 0.0
            self.monthly_usage = 0.0

            logger.info(f"Usage data reset (backup saved to {backup_file})")

        except Exception as e:
            logger.error(f"Failed to reset usage data: {e}")

    def get_cost_trends(self, days: int = 30) -> Dict[str, List[float]]:
        """Get cost trends over specified days"""
        now = time.time()
        day_seconds = 24 * 60 * 60

        trends = {
            "daily_costs": [],
            "dates": []
        }

        for i in range(days):
            day_start = now - (i + 1) * day_seconds
            day_end = now - i * day_seconds

            daily_cost = sum(
                entry.cost for entry in self.cost_entries
                if day_start <= entry.timestamp < day_end
            )

            trends["daily_costs"].insert(0, daily_cost)
            trends["dates"].insert(0, datetime.fromtimestamp(day_start).strftime("%Y-%m-%d"))

        return trends