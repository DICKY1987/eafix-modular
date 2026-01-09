# DOC_ID: DOC-SERVICE-0085
"""
System Health Aggregator

Aggregates health data from all services to provide system-wide health status,
trend analysis, and overall system health scoring.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


class SystemHealthAggregator:
    """Aggregates health data across all monitored services."""
    
    def __init__(self, settings, metrics):
        self.settings = settings
        self.metrics = metrics
        
        # System health history
        self.system_health_history: List[Dict[str, Any]] = []
        self._history_lock = asyncio.Lock()
        
        # Service availability tracking
        self.service_availability: Dict[str, List[bool]] = {}
        
        self.running = False
    
    async def start(self) -> None:
        """Start the system health aggregator."""
        self.running = True
        logger.info("System health aggregator started")
    
    async def stop(self) -> None:
        """Stop the system health aggregator."""
        self.running = False
        logger.info("System health aggregator stopped")
    
    async def aggregate_system_health(self) -> Dict[str, Any]:
        """Aggregate health data from all services into system-wide health status."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info("Starting system health aggregation")
            
            # Get health data from collector (would be passed in real implementation)
            # For now, simulate this by calling the collector directly
            from .collector import HealthMetricsCollector
            
            # In a real implementation, this would be dependency-injected
            # For now, we'll aggregate based on available data
            
            aggregation_result = await self._perform_aggregation()
            
            # Store in history
            await self._store_aggregation_result(aggregation_result)
            
            aggregation_time = asyncio.get_event_loop().time() - start_time
            self.metrics.record_aggregation(aggregation_time)
            
            logger.info(
                "System health aggregation completed",
                overall_status=aggregation_result.get("overall_status"),
                healthy_services=aggregation_result.get("healthy_services", 0),
                total_services=aggregation_result.get("total_services", 0),
                time_seconds=aggregation_time
            )
            
            return aggregation_result
            
        except Exception as e:
            aggregation_time = asyncio.get_event_loop().time() - start_time
            logger.error("System health aggregation failed", error=str(e), exc_info=True)
            self.metrics.record_aggregation(aggregation_time)
            self.metrics.record_error("aggregation_error")
            
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _perform_aggregation(self) -> Dict[str, Any]:
        """Perform the actual health aggregation logic."""
        timestamp = datetime.utcnow()
        
        # Simulate service health data (in real implementation, get from collector)
        service_health_data = await self._get_current_service_health()
        
        # Calculate service-level health scores
        service_scores = {}
        healthy_services = 0
        degraded_services = 0
        unhealthy_services = 0
        
        for service_name, health_data in service_health_data.items():
            health_score = health_data.get("health_score", 0.0)
            overall_healthy = health_data.get("overall_healthy", False)
            
            service_scores[service_name] = {
                "health_score": health_score,
                "status": self._determine_service_status(health_score, overall_healthy),
                "last_check": health_data.get("timestamp"),
                "weight": self.settings.get_service_weight(service_name)
            }
            
            # Count service states
            status = service_scores[service_name]["status"]
            if status == "healthy":
                healthy_services += 1
            elif status == "degraded":
                degraded_services += 1
            else:
                unhealthy_services += 1
            
            # Track availability
            await self._update_service_availability(service_name, overall_healthy)
        
        # Calculate weighted system health score
        system_health_score = self._calculate_weighted_system_score(service_scores)
        
        # Determine overall system status
        overall_status = self._determine_system_status(
            system_health_score, healthy_services, len(service_health_data)
        )
        
        # Calculate system trends
        trends = await self._calculate_system_trends()
        
        # Generate service alerts
        service_alerts = self._generate_service_alerts(service_scores)
        
        # Calculate availability percentages
        availability_stats = await self._calculate_availability_stats()
        
        aggregation_result = {
            "success": True,
            "timestamp": timestamp.isoformat(),
            
            # Overall system health
            "overall_status": overall_status,
            "system_health_score": system_health_score,
            
            # Service counts
            "total_services": len(service_health_data),
            "healthy_services": healthy_services,
            "degraded_services": degraded_services,
            "unhealthy_services": unhealthy_services,
            "healthy_percentage": (healthy_services / len(service_health_data)) * 100 if service_health_data else 0,
            
            # Detailed service information
            "service_health": service_scores,
            "service_alerts": service_alerts,
            "availability_stats": availability_stats,
            
            # System trends
            "trends": trends,
            
            # System configuration
            "minimum_healthy_threshold": self.settings.minimum_healthy_services_percent,
            "service_weights": self.settings.service_weight_override
        }
        
        return aggregation_result
    
    async def _get_current_service_health(self) -> Dict[str, Any]:
        """Get current health data for all services (placeholder implementation)."""
        # In a real implementation, this would get data from the collector
        # For now, simulate basic health data
        
        services = self.settings.monitored_services.keys()
        service_health = {}
        
        for service_name in services:
            # Simulate health data
            health_score = 0.8  # Default healthy score
            if service_name in ["data-ingestor", "execution-engine"]:
                health_score = 0.9  # Critical services are healthier
            elif service_name in ["gui-gateway", "reporter"]:
                health_score = 0.7  # Less critical services might have issues
            
            service_health[service_name] = {
                "health_score": health_score,
                "overall_healthy": health_score > 0.6,
                "timestamp": datetime.utcnow().isoformat(),
                "service": service_name
            }
        
        return service_health
    
    def _determine_service_status(self, health_score: float, overall_healthy: bool) -> str:
        """Determine service status based on health score and overall health."""
        if not overall_healthy:
            return "unhealthy"
        elif health_score >= 0.8:
            return "healthy"
        elif health_score >= 0.6:
            return "degraded"
        else:
            return "unhealthy"
    
    def _calculate_weighted_system_score(self, service_scores: Dict[str, Dict[str, Any]]) -> float:
        """Calculate weighted system health score."""
        if not service_scores:
            return 0.0
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for service_name, data in service_scores.items():
            health_score = data["health_score"]
            weight = data["weight"]
            
            total_weighted_score += health_score * weight
            total_weight += weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _determine_system_status(self, system_score: float, healthy_services: int, total_services: int) -> str:
        """Determine overall system status."""
        if total_services == 0:
            return "unknown"
        
        healthy_percentage = (healthy_services / total_services) * 100
        
        # Check minimum healthy threshold
        if healthy_percentage < self.settings.minimum_healthy_services_percent:
            return "critical"
        elif system_score >= 0.8 and healthy_percentage >= 90:
            return "healthy"
        elif system_score >= 0.6 and healthy_percentage >= 70:
            return "degraded"
        else:
            return "unhealthy"
    
    async def _update_service_availability(self, service_name: str, is_healthy: bool) -> None:
        """Update service availability tracking."""
        if service_name not in self.service_availability:
            self.service_availability[service_name] = []
        
        self.service_availability[service_name].append(is_healthy)
        
        # Keep only recent availability data (last 100 checks)
        if len(self.service_availability[service_name]) > 100:
            self.service_availability[service_name] = self.service_availability[service_name][-100:]
    
    async def _calculate_system_trends(self) -> Dict[str, Any]:
        """Calculate system health trends over time."""
        async with self._history_lock:
            if len(self.system_health_history) < 2:
                return {
                    "trend_available": False,
                    "message": "Insufficient historical data"
                }
            
            current = self.system_health_history[-1]
            previous = self.system_health_history[-2]
            
            # Calculate trends
            score_trend = current.get("system_health_score", 0) - previous.get("system_health_score", 0)
            healthy_services_trend = current.get("healthy_services", 0) - previous.get("healthy_services", 0)
            
            # Status change
            status_change = current.get("overall_status") != previous.get("overall_status")
            
            return {
                "trend_available": True,
                "score_trend": score_trend,
                "score_direction": "improving" if score_trend > 0 else "declining" if score_trend < 0 else "stable",
                "healthy_services_trend": healthy_services_trend,
                "status_changed": status_change,
                "previous_status": previous.get("overall_status"),
                "current_status": current.get("overall_status"),
                "data_points": len(self.system_health_history)
            }
    
    def _generate_service_alerts(self, service_scores: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate alerts based on service health scores."""
        alerts = []
        
        for service_name, data in service_scores.items():
            health_score = data["health_score"]
            status = data["status"]
            
            if status == "unhealthy":
                alerts.append({
                    "service": service_name,
                    "severity": "critical",
                    "message": f"Service {service_name} is unhealthy (score: {health_score:.2f})",
                    "health_score": health_score,
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif status == "degraded":
                alerts.append({
                    "service": service_name,
                    "severity": "warning",
                    "message": f"Service {service_name} is degraded (score: {health_score:.2f})",
                    "health_score": health_score,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return alerts
    
    async def _calculate_availability_stats(self) -> Dict[str, Any]:
        """Calculate availability statistics for all services."""
        availability_stats = {}
        
        for service_name, availability_data in self.service_availability.items():
            if not availability_data:
                continue
            
            total_checks = len(availability_data)
            healthy_checks = sum(availability_data)
            availability_percentage = (healthy_checks / total_checks) * 100
            
            # Calculate recent availability (last 10 checks)
            recent_data = availability_data[-10:]
            recent_healthy = sum(recent_data)
            recent_availability = (recent_healthy / len(recent_data)) * 100 if recent_data else 0
            
            availability_stats[service_name] = {
                "overall_availability": availability_percentage,
                "recent_availability": recent_availability,
                "total_checks": total_checks,
                "healthy_checks": healthy_checks,
                "weight": self.settings.get_service_weight(service_name)
            }
        
        return availability_stats
    
    async def _store_aggregation_result(self, result: Dict[str, Any]) -> None:
        """Store aggregation result in history."""
        async with self._history_lock:
            self.system_health_history.append(result)
            
            # Keep only recent history (last 1000 entries)
            if len(self.system_health_history) > 1000:
                self.system_health_history = self.system_health_history[-1000:]
    
    async def get_system_health_overview(self) -> Dict[str, Any]:
        """Get comprehensive system health overview."""
        async with self._history_lock:
            if not self.system_health_history:
                return {
                    "available": False,
                    "message": "No system health data available"
                }
            
            latest = self.system_health_history[-1]
            
            # Add historical context
            overview = latest.copy()
            overview.update({
                "historical_data_points": len(self.system_health_history),
                "first_aggregation": self.system_health_history[0]["timestamp"] if self.system_health_history else None,
                "last_updated": latest["timestamp"]
            })
            
            return overview
    
    async def get_service_availability_report(self) -> Dict[str, Any]:
        """Get detailed service availability report."""
        availability_stats = await self._calculate_availability_stats()
        
        # Calculate system-wide availability
        if availability_stats:
            weighted_availability = 0.0
            total_weight = 0.0
            
            for service_name, stats in availability_stats.items():
                weight = stats["weight"]
                availability = stats["overall_availability"]
                
                weighted_availability += availability * weight
                total_weight += weight
            
            system_availability = weighted_availability / total_weight if total_weight > 0 else 0.0
        else:
            system_availability = 0.0
        
        return {
            "system_availability": system_availability,
            "service_availability": availability_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get aggregator status."""
        async with self._history_lock:
            history_count = len(self.system_health_history)
        
        return {
            "running": self.running,
            "system_health_history_count": history_count,
            "service_availability_tracked": len(self.service_availability),
            "aggregation_enabled": self.settings.system_aggregation_enabled,
            "aggregation_interval": self.settings.aggregation_interval_seconds
        }