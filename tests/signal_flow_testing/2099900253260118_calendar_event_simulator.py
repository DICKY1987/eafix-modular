#!/usr/bin/env python3
# doc_id: DOC-TEST-0073
"""
Manual Economic Calendar Signal Simulator.

Creates current-shape ActiveCalendarSignal CSV files for signal-flow tests.
"""

import csv
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List


ACTIVE_SIGNAL_FIELDS = [
    "file_seq",
    "checksum_sha256",
    "timestamp",
    "calendar_id",
    "symbol",
    "impact_level",
    "proximity_state",
    "anticipation_event",
    "direction_bias",
    "confidence_score",
]


class CalendarEventSimulator:
    """Simulates current-shape active calendar signals for testing."""

    def __init__(self, csv_dir: str = None):
        self.csv_dir = Path(csv_dir) if csv_dir else Path.cwd() / "test_data"
        self.csv_dir.mkdir(exist_ok=True)
        self.file_seq = 1

    def create_test_event(self, event_config: Dict) -> Dict:
        """Create a single ActiveCalendarSignal row."""
        now = datetime.now(timezone.utc)
        minutes_from_now = int(event_config.get("minutes_from_now", 30))
        event_time = now + timedelta(minutes=minutes_from_now)

        proximity_state = event_config.get("proximity_state")
        if not proximity_state:
            if minutes_from_now > 5:
                proximity_state = "PRE_1H"
            elif minutes_from_now >= -5:
                proximity_state = "AT_EVENT"
            else:
                proximity_state = "POST_30M"

        impact_level = event_config.get("impact_level")
        if not impact_level:
            raw_impact = str(event_config.get("impact", "HIGH")).upper()
            impact_level = "HIGH" if raw_impact in {"H", "HIGH"} else "MEDIUM"

        currency = event_config.get("currency") or event_config.get("country", "US")
        currency = "USD" if currency == "US" else str(currency).upper()[:3]
        event_code = event_config.get("event_code") or event_config.get("event_type", "NFP")
        calendar_id = event_config.get("calendar_id") or f"CAL8_{currency}_{event_code}_H"

        signal = {
            "file_seq": self.file_seq,
            "timestamp": event_time.isoformat().replace("+00:00", "Z"),
            "calendar_id": calendar_id,
            "symbol": event_config.get("symbol", "EURUSD"),
            "impact_level": impact_level,
            "proximity_state": proximity_state,
            "anticipation_event": proximity_state == "PRE_1H",
            "direction_bias": event_config.get("direction_bias", "BULLISH"),
            "confidence_score": float(event_config.get("confidence_score", 0.85)),
        }
        signal["checksum_sha256"] = self._compute_row_checksum(signal)
        return signal

    def write_active_calendar_signals(self, events: List[Dict]) -> str:
        """Write ActiveCalendarSignal rows with an atomic temp-file rename."""
        temp_file = self.csv_dir / "active_calendar_signals.csv.tmp"
        final_file = self.csv_dir / "active_calendar_signals.csv"

        with temp_file.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=ACTIVE_SIGNAL_FIELDS)
            writer.writeheader()
            writer.writerows(
                {field: event.get(field) for field in ACTIVE_SIGNAL_FIELDS}
                for event in events
            )

        temp_file.rename(final_file)
        self.file_seq += 1
        return str(final_file)

    def simulate_event_lifecycle(
        self,
        symbol: str = "EURUSD",
        minutes_ahead: int = 30,
    ) -> List[str]:
        """Simulate PRE_1H -> AT_EVENT -> POST_30M signal lifecycle."""
        stages = [
            ("PRE_1H", minutes_ahead),
            ("AT_EVENT", 0),
            ("POST_30M", -10),
        ]

        created_files = []
        for proximity_state, minutes_from_now in stages:
            event = self.create_test_event({
                "symbol": symbol,
                "currency": "USD",
                "impact_level": "HIGH",
                "event_code": "NFP",
                "proximity_state": proximity_state,
                "minutes_from_now": minutes_from_now,
                "confidence_score": 0.9 if proximity_state == "AT_EVENT" else 0.8,
            })
            created_files.append(self.write_active_calendar_signals([event]))
        return created_files

    def create_multiple_events(self, event_configs: List[Dict]) -> str:
        """Create multiple ActiveCalendarSignal rows in a single CSV file."""
        return self.write_active_calendar_signals([
            self.create_test_event(config) for config in event_configs
        ])

    def _compute_row_checksum(self, row_data: Dict) -> str:
        values = [
            str(row_data[key])
            for key in sorted(row_data.keys())
            if key != "checksum_sha256"
        ]
        return hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()


def main() -> None:
    simulator = CalendarEventSimulator()
    file_path = simulator.create_multiple_events([
        {
            "symbol": "EURUSD",
            "currency": "USD",
            "event_code": "NFP",
            "proximity_state": "PRE_1H",
        },
        {
            "symbol": "GBPUSD",
            "currency": "GBP",
            "event_code": "BOE",
            "proximity_state": "AT_EVENT",
        },
    ])
    print(f"Created current-shape active calendar signals: {file_path}")


if __name__ == "__main__":
    main()

