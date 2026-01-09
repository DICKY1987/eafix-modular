#!/usr/bin/env python3
# DOC_ID: DOC-SERVICE-0027
"""
Calendar Downloader Service - Enterprise Edition
Automated ForexFactory calendar download with BaseEnterpriseService capabilities
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from pathlib import Path

from services.common.base_service import BaseEnterpriseService
from .ff_auto_downloader import ForexFactoryDownloader
from .python_calendar_system_patched import CalendarProcessor


class CalendarDownloaderService(BaseEnterpriseService):
    """Enterprise calendar downloader with automated ForexFactory integration"""

    def __init__(self):
        super().__init__(service_name="calendar-downloader")
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.downloader = None
        self.processor = None
        self.download_path = Path("data/calendars")
        self.download_path.mkdir(parents=True, exist_ok=True)

        # Download schedule configuration
        self.download_interval = 3600  # 1 hour
        self.download_task = None

    async def startup(self):
        """Initialize calendar downloader service"""
        try:
            self.logger.info("Starting calendar downloader service...")

            # Initialize ForexFactory downloader
            self.downloader = ForexFactoryDownloader(
                download_path=str(self.download_path),
                user_agent="EAFIX-CalendarDownloader/1.0"
            )

            # Initialize calendar processor
            self.processor = CalendarProcessor(
                calendar_directory=str(self.download_path)
            )

            # Start periodic download task
            self.download_task = asyncio.create_task(self._download_loop())

            self.logger.info("Calendar downloader service started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start calendar downloader: {e}")
            raise

    async def shutdown(self):
        """Graceful shutdown of calendar downloader service"""
        try:
            self.logger.info("Shutting down calendar downloader service...")

            # Cancel download task
            if self.download_task:
                self.download_task.cancel()
                try:
                    await self.download_task
                except asyncio.CancelledError:
                    pass

            self.logger.info("Calendar downloader service shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Health check for calendar downloader service"""
        health_status = {
            "service": "calendar-downloader",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "downloader": "healthy" if self.downloader else "unhealthy",
                "processor": "healthy" if self.processor else "unhealthy",
                "download_task": "running" if self.download_task and not self.download_task.done() else "stopped"
            },
            "metrics": {
                "download_path": str(self.download_path),
                "download_interval": self.download_interval
            }
        }

        # Check if download directory is accessible
        try:
            if not self.download_path.exists():
                health_status["status"] = "degraded"
                health_status["components"]["download_path"] = "missing"
        except Exception:
            health_status["status"] = "unhealthy"
            health_status["components"]["download_path"] = "inaccessible"

        return health_status

    async def _download_loop(self):
        """Periodic calendar download loop"""
        while True:
            try:
                self.logger.info("Starting calendar download cycle...")

                # Download current week's calendar
                current_date = datetime.now()
                week_start = current_date - timedelta(days=current_date.weekday())
                week_end = week_start + timedelta(days=6)

                # Track download metrics
                download_start = datetime.utcnow()

                try:
                    # Perform download
                    result = await self._download_calendar(week_start, week_end)

                    # Update metrics
                    download_duration = (datetime.utcnow() - download_start).total_seconds()
                    self.metrics.request_duration.observe(download_duration)
                    self.metrics.request_count.labels(
                        method="download",
                        endpoint="forexfactory",
                        status="success"
                    ).inc()

                    self.logger.info(f"Calendar download completed in {download_duration:.2f}s")

                except Exception as e:
                    self.metrics.request_count.labels(
                        method="download",
                        endpoint="forexfactory",
                        status="error"
                    ).inc()
                    self.logger.error(f"Calendar download failed: {e}")

                # Wait for next download cycle
                await asyncio.sleep(self.download_interval)

            except asyncio.CancelledError:
                self.logger.info("Download loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in download loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry

    async def _download_calendar(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Download and process calendar for date range"""
        try:
            # Download calendar data
            calendar_data = self.downloader.download_week(start_date, end_date)

            # Process calendar data
            if calendar_data:
                processed_events = self.processor.process_calendar_data(calendar_data)
                return {
                    "success": True,
                    "events_count": len(processed_events),
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "No calendar data retrieved"
                }

        except Exception as e:
            self.logger.error(f"Calendar download/processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# FastAPI application setup
from fastapi import FastAPI

app = FastAPI(
    title="EAFIX Calendar Downloader",
    description="Automated ForexFactory economic calendar downloader",
    version="1.0.0"
)

# Initialize service
calendar_service = CalendarDownloaderService()

# Add enterprise endpoints
app.add_api_route("/healthz", calendar_service.health_check)
app.add_api_route("/readyz", calendar_service.health_check)
app.add_api_route("/metrics", calendar_service.get_metrics)

@app.on_event("startup")
async def startup_event():
    await calendar_service.startup()

@app.on_event("shutdown")
async def shutdown_event():
    await calendar_service.shutdown()

# Manual download endpoint
@app.post("/download/manual")
async def manual_download():
    """Trigger manual calendar download"""
    try:
        current_date = datetime.now()
        week_start = current_date - timedelta(days=current_date.weekday())
        week_end = week_start + timedelta(days=6)

        result = await calendar_service._download_calendar(week_start, week_end)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)