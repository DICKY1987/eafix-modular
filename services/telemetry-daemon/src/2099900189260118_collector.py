# doc_id: DOC-SERVICE-0174
# DOC_ID: DOC-SERVICE-0087
"""
Health Metrics Collector

Collects health metrics from all monitored services, validates data,
and stores metrics using the HealthMetric contract model with atomic CSV writes.
"""

import asyncio
import csv
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import httpx
import structlog

# Add contracts to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "contracts"))

from contracts.models import HealthMetric

logger = structlog.get_logger(__name__)


class HealthMetricsCollector:
    """Collects health metrics from monitored services."""
    
    def __init__(self, settings, metrics):
        self.settings = settings
        self.metrics = metrics
        
        # HTTP clients for service health checks
        self.http_clients: Dict[str, httpx.AsyncClient] = {}
        
        # Health data storage
        self.health_data: Dict[str, List[Dict[str, Any]]] = {}
        self._health_data_lock = asyncio.Lock()
        
        # CSV sequence tracking
        self.csv_sequence = 1
        self._sequence_lock = asyncio.Lock()
        
        self.running = False
    
    async def start(self) -> None:
        """Start the health metrics collector."""
        # Initialize HTTP clients for all monitored services
        timeout = httpx.Timeout(self.settings.service_timeout_seconds)
        
        for service_name, endpoint in self.settings.monitored_services.items():
            self.http_clients[service_name] = httpx.AsyncClient(
                base_url=endpoint,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
        
        self.running = True
        logger.info(
            "Health metrics collector started",
            monitored_services=list(self.settings.monitored_services.keys())
        )
    
    async def stop(self) -> None:
        """Stop the health metrics collector."""
        # Close all HTTP clients
        for client in self.http_clients.values():
            await client.aclose()
        
        self.http_clients.clear()
        self.running = False
        logger.info("Health metrics collector stopped")
    
    async def collect_all_service_health(self) -> Dict[str, Any]:
        """Collect health metrics from all monitored services."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info("Starting health collection cycle")
            
            # Collect health from all services concurrently
            collection_tasks = []
            for service_name in self.settings.monitored_services.keys():
                task = asyncio.create_task(
                    self._collect_service_health(service_name)
                )
                collection_tasks.append((service_name, task))
            
            # Wait for all collections to complete
            results = {}
            successful_collections = 0
            
            for service_name, task in collection_tasks:
                try:
                    health_data = await task
                    results[service_name] = health_data
                    
                    if health_data and health_data.get("success", False):
                        successful_collections += 1
                        await self._store_health_data(service_name, health_data)
                        
                except Exception as e:
                    logger.error(
                        "Service health collection failed",
                        service=service_name,
                        error=str(e)
                    )
                    results[service_name] = {
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    self.metrics.record_error("health_collection_error")
            
            collection_time = asyncio.get_event_loop().time() - start_time
            
            summary = {
                "success": True,
                "total_services": len(self.settings.monitored_services),
                "successful_collections": successful_collections,
                "failed_collections": len(self.settings.monitored_services) - successful_collections,
                "collection_time_seconds": collection_time,
                "timestamp": datetime.utcnow().isoformat(),
                "results": results
            }
            
            # Record metrics
            self.metrics.record_health_collection(collection_time, successful_collections)
            
            logger.info(
                "Health collection cycle completed",
                successful=successful_collections,
                failed=summary["failed_collections"],
                time_seconds=collection_time
            )
            
            return summary
            
        except Exception as e:
            collection_time = asyncio.get_event_loop().time() - start_time
            logger.error("Health collection cycle failed", error=str(e), exc_info=True)
            self.metrics.record_health_collection(collection_time, 0)
            
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _collect_service_health(self, service_name: str) -> Dict[str, Any]:
        """Collect health metrics from a specific service."""
        if service_name not in self.http_clients:
            return {
                "success": False,
                "error": "Service not configured",
                "service": service_name
            }
        
        client = self.http_clients[service_name]
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Try multiple endpoints for comprehensive health data
            health_data = {}
            
            # Basic health check
            try:
                response = await client.get("/healthz")
                health_data["basic_health"] = {
                    "status_code": response.status_code,
                    "healthy": response.status_code == 200,
                    "response_time_ms": (asyncio.get_event_loop().time() - start_time) * 1000
                }
            except Exception as e:
                health_data["basic_health"] = {
                    "healthy": False,
                    "error": str(e),
                    "response_time_ms": (asyncio.get_event_loop().time() - start_time) * 1000
                }
            
            # Detailed readiness check
            try:
                response = await client.get("/readyz")
                if response.status_code == 200:
                    readiness_data = response.json()
                    health_data["readiness"] = readiness_data
                else:
                    health_data["readiness"] = {
                        "ready": False,
                        "status_code": response.status_code
                    }
            except Exception as e:
                health_data["readiness"] = {
                    "ready": False,
                    "error": str(e)
                }
            
            # Service-specific metrics
            try:
                response = await client.get("/metrics")
                if response.status_code == 200:
                    metrics_data = response.json()
                    health_data["metrics"] = metrics_data
            except Exception as e:
                health_data["metrics"] = {
                    "available": False,
                    "error": str(e)
                }
            
            # Calculate overall health score
            overall_healthy = health_data.get("basic_health", {}).get("healthy", False)
            ready = health_data.get("readiness", {}).get("ready", False)
            
            result = {
                "success": True,
                "service": service_name,
                "timestamp": datetime.utcnow().isoformat(),
                "overall_healthy": overall_healthy,
                "ready": ready,
                "health_score": self._calculate_health_score(health_data),
                "data": health_data
            }
            
            self.metrics.record_service_health_check(
                service_name,
                (asyncio.get_event_loop().time() - start_time),
                overall_healthy
            )
            
            return result
            
        except Exception as e:
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            logger.error(
                "Service health check failed",
                service=service_name,
                error=str(e)
            )
            
            self.metrics.record_service_health_check(
                service_name,
                (asyncio.get_event_loop().time() - start_time),
                False
            )
            
            return {
                "success": False,
                "service": service_name,
                "error": str(e),
                "response_time_ms": response_time,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _calculate_health_score(self, health_data: Dict[str, Any]) -> float:
        """Calculate a health score (0.0 to 1.0) based on health data."""
        score = 0.0
        max_score = 0.0
        
        # Basic health check (40% weight)
        max_score += 0.4
        basic_health = health_data.get("basic_health", {})
        if basic_health.get("healthy", False):
            score += 0.4
        
        # Readiness (30% weight)
        max_score += 0.3
        readiness = health_data.get("readiness", {})
        if readiness.get("ready", False):
            score += 0.3
        
        # Metrics availability (10% weight)
        max_score += 0.1
        metrics_data = health_data.get("metrics", {})
        if metrics_data and not metrics_data.get("error"):
            score += 0.1
        
        # Response time (20% weight - penalize slow responses)
        max_score += 0.2
        response_time = basic_health.get("response_time_ms", 0)
        if response_time > 0:
            if response_time < 100:
                score += 0.2
            elif response_time < 500:
                score += 0.15
            elif response_time < 1000:
                score += 0.1
            elif response_time < 2000:
                score += 0.05
            # No points for response time > 2000ms
        
        return score / max_score if max_score > 0 else 0.0
    
    async def _store_health_data(self, service_name: str, health_data: Dict[str, Any]) -> None:
        """Store health data for a service."""
        async with self._health_data_lock:
            if service_name not in self.health_data:
                self.health_data[service_name] = []
            
            self.health_data[service_name].append(health_data)
            
            # Keep only recent data
            retention_hours = self.settings.health_metrics_retention_hours
            cutoff_time = datetime.utcnow() - timedelta(hours=retention_hours)
            
            self.health_data[service_name] = [
                data for data in self.health_data[service_name]
                if datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00')) > cutoff_time
            ]
        
        # Write to CSV if enabled
        if self.settings.csv_output_enabled:
            await self._write_health_metric_csv(service_name, health_data)
    
    async def _write_health_metric_csv(self, service_name: str, health_data: Dict[str, Any]) -> None:
        """Write health metric to CSV using atomic writes."""
        try:
            output_dir = self.settings.get_output_path()
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H")
            csv_filename = f"health_metrics_{timestamp_str}.csv"
            csv_filepath = output_dir / csv_filename
            
            # Get next sequence number
            async with self._sequence_lock:
                file_seq = self.csv_sequence
                self.csv_sequence += 1
            
            # Extract key metrics for CSV
            basic_health = health_data.get("data", {}).get("basic_health", {})
            readiness = health_data.get("data", {}).get("readiness", {})
            metrics_info = health_data.get("data", {}).get("metrics", {})
            
            # Create HealthMetric model
            csv_record = HealthMetric(
                file_seq=file_seq,
                timestamp=datetime.utcnow(),
                checksum_sha256="placeholder",  # Will be computed
                
                service_name=service_name,
                metric_name="overall_health",
                metric_value=health_data.get("health_score", 0.0),
                metric_unit="score",
                health_status="HEALTHY" if health_data.get("overall_healthy", False) else "UNHEALTHY",
                cpu_usage_percent=self._extract_metric(metrics_info, "cpu_usage", 0.0),
                memory_usage_percent=self._extract_metric(metrics_info, "memory_usage", 0.0),
                disk_usage_percent=self._extract_metric(metrics_info, "disk_usage", 0.0)
            )
            
            # Compute checksum
            csv_record.checksum_sha256 = csv_record.compute_checksum()
            
            # Verify checksum
            if not csv_record.verify_checksum():
                raise ValueError("Checksum verification failed")
            
            # Atomic write process
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.tmp',
                dir=output_dir,
                delete=False,
                newline=''
            ) as tmp_file:
                
                writer = csv.writer(tmp_file)
                
                # Write header if new file
                if not csv_filepath.exists():
                    header = [
                        "file_seq", "checksum_sha256", "timestamp", "service_name",
                        "metric_name", "metric_value", "metric_unit", "health_status",
                        "cpu_usage_percent", "memory_usage_percent", "disk_usage_percent"
                    ]
                    writer.writerow(header)
                
                # Write data row
                row = [
                    csv_record.file_seq, csv_record.checksum_sha256, csv_record.timestamp.isoformat(),
                    csv_record.service_name, csv_record.metric_name, csv_record.metric_value,
                    csv_record.metric_unit, csv_record.health_status, csv_record.cpu_usage_percent,
                    csv_record.memory_usage_percent, csv_record.disk_usage_percent
                ]
                writer.writerow(row)
                
                # Ensure data is written to disk
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                tmp_filepath = Path(tmp_file.name)
            
            # Atomic rename to final filename
            if csv_filepath.exists():
                # Append to existing file
                with open(csv_filepath, 'a', newline='') as f:
                    with open(tmp_filepath, 'r') as tmp_f:
                        lines = tmp_f.readlines()
                        if len(lines) > 1:  # Has header + data
                            f.write(lines[-1])  # Write only the data line
                        elif len(lines) == 1:  # Only data line
                            f.write(lines[0])
                tmp_filepath.unlink()
            else:
                tmp_filepath.rename(csv_filepath)
            
            self.metrics.increment_counter("csv_writes_total")
            
        except Exception as e:
            logger.error("Failed to write health metric CSV", service=service_name, error=str(e))
            self.metrics.record_error("csv_write_error")
    
    def _extract_metric(self, metrics_data: Dict[str, Any], metric_name: str, default: float) -> float:
        """Extract a specific metric value from metrics data."""
        try:
            if not metrics_data or "error" in metrics_data:
                return default
            
            # Try to find metric in various formats
            if metric_name in metrics_data:
                return float(metrics_data[metric_name])
            
            # Try nested structures
            system_metrics = metrics_data.get("system", {})
            if metric_name in system_metrics:
                return float(system_metrics[metric_name])
            
            return default
            
        except (ValueError, TypeError):
            return default
    
    async def get_service_health_details(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed health information for a specific service."""
        async with self._health_data_lock:
            if service_name not in self.health_data:
                return None
            
            recent_data = self.health_data[service_name]
            if not recent_data:
                return None
            
            # Get most recent health data
            latest = recent_data[-1]
            
            # Calculate trends over time
            if len(recent_data) > 1:
                previous = recent_data[-2]
                trend = {
                    "health_score_change": latest.get("health_score", 0) - previous.get("health_score", 0),
                    "status_change": latest.get("overall_healthy") != previous.get("overall_healthy")
                }
            else:
                trend = {"health_score_change": 0, "status_change": False}
            
            return {
                "service": service_name,
                "latest_health": latest,
                "historical_count": len(recent_data),
                "trend": trend,
                "first_seen": recent_data[0]["timestamp"] if recent_data else None,
                "last_updated": latest["timestamp"]
            }
    
    async def ingest_health_data(self, health_data: Dict[str, Any]) -> None:
        """Manually ingest health data (for external sources)."""
        service_name = health_data.get("service", "external")
        
        # Add timestamp if not present
        if "timestamp" not in health_data:
            health_data["timestamp"] = datetime.utcnow().isoformat()
        
        await self._store_health_data(service_name, health_data)
        self.metrics.increment_counter("manual_health_ingestions")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get health collector status."""
        async with self._health_data_lock:
            service_counts = {
                service: len(data) for service, data in self.health_data.items()
            }
        
        return {
            "running": self.running,
            "monitored_services": len(self.settings.monitored_services),
            "http_clients": len(self.http_clients),
            "csv_sequence": self.csv_sequence,
            "health_data_counts": service_counts,
            "total_health_records": sum(service_counts.values())
        }