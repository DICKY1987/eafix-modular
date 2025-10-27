"""
Alert Management System

Manages alerts based on health thresholds, implements alert cooldown,
notification channels, and alert history tracking.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict

import redis.asyncio as redis
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Alert:
    """Alert data structure."""
    
    id: str
    service_name: str
    metric_name: str
    severity: str  # "critical", "warning", "info"
    message: str
    value: float
    threshold: float
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        """Create alert from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data.get('resolved_at'):
            data['resolved_at'] = datetime.fromisoformat(data['resolved_at'])
        return cls(**data)


class AlertManager:
    """Manages system alerts, thresholds, and notifications."""
    
    def __init__(self, settings, metrics):
        self.settings = settings
        self.metrics = metrics
        
        # Redis client for publishing alerts
        self.redis_client: Optional[redis.Redis] = None
        
        # Active alerts storage
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self._alerts_lock = asyncio.Lock()
        
        # Alert cooldown tracking
        self.alert_cooldowns: Dict[str, datetime] = {}
        
        # Threshold overrides
        self.threshold_overrides: Dict[str, Dict[str, Dict[str, float]]] = {}
        
        self.running = False
    
    async def start(self) -> None:
        """Start the alert manager."""
        # Initialize Redis connection
        self.redis_client = redis.from_url(self.settings.redis_url)
        
        self.running = True
        logger.info("Alert manager started")
    
    async def stop(self) -> None:
        """Stop the alert manager."""
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        self.running = False
        logger.info("Alert manager stopped")
    
    async def process_alerts(self) -> None:
        """Main alert processing loop."""
        try:
            logger.debug("Starting alert processing cycle")
            
            # Get current system health data
            health_data = await self._get_current_health_data()
            
            # Process each service's health metrics
            alerts_generated = 0
            alerts_resolved = 0
            
            for service_name, metrics_data in health_data.items():
                service_alerts = await self._evaluate_service_alerts(service_name, metrics_data)
                alerts_generated += len(service_alerts)
                
                # Process new alerts
                for alert in service_alerts:
                    await self._process_alert(alert)
            
            # Check for resolved alerts
            resolved_count = await self._check_resolved_alerts(health_data)
            alerts_resolved += resolved_count
            
            # Clean up old alerts
            await self._cleanup_old_alerts()
            
            logger.info(
                "Alert processing cycle completed",
                alerts_generated=alerts_generated,
                alerts_resolved=alerts_resolved,
                active_alerts=len(self.active_alerts)
            )
            
        except Exception as e:
            logger.error("Alert processing failed", error=str(e), exc_info=True)
            self.metrics.record_error("alert_processing_error")
    
    async def _get_current_health_data(self) -> Dict[str, Dict[str, Any]]:
        """Get current health data for all services (placeholder)."""
        # In real implementation, this would get data from the health collector
        # For now, simulate some health data for alerting
        
        services = self.settings.monitored_services.keys()
        health_data = {}
        
        for service_name in services:
            # Simulate health metrics that might trigger alerts
            health_data[service_name] = {
                "response_time_ms": 500.0 if service_name != "execution-engine" else 2500.0,
                "cpu_usage_percent": 70.0 if service_name != "risk-manager" else 90.0,
                "memory_usage_percent": 75.0,
                "disk_usage_percent": 60.0,
                "error_rate_percent": 2.0 if service_name != "signal-generator" else 8.0,
                "uptime_hours": 24.0,
                "overall_healthy": True if service_name not in ["execution-engine", "risk-manager"] else False
            }
        
        return health_data
    
    async def _evaluate_service_alerts(self, service_name: str, metrics_data: Dict[str, Any]) -> List[Alert]:
        """Evaluate alerts for a specific service."""
        alerts = []
        
        # Get thresholds for this service
        thresholds = self._get_service_thresholds(service_name)
        
        # Check each metric against its thresholds
        for metric_name, metric_value in metrics_data.items():
            if metric_name in thresholds and isinstance(metric_value, (int, float)):
                metric_thresholds = thresholds[metric_name]
                
                # Check critical threshold
                if metric_value >= metric_thresholds.get("critical", float('inf')):
                    alert = self._create_alert(
                        service_name, metric_name, "critical",
                        metric_value, metric_thresholds["critical"]
                    )
                    alerts.append(alert)
                
                # Check warning threshold (only if not critical)
                elif metric_value >= metric_thresholds.get("warning", float('inf')):
                    alert = self._create_alert(
                        service_name, metric_name, "warning",
                        metric_value, metric_thresholds["warning"]
                    )
                    alerts.append(alert)
        
        return alerts
    
    def _get_service_thresholds(self, service_name: str) -> Dict[str, Dict[str, float]]:
        """Get thresholds for a service, including overrides."""
        # Start with default thresholds
        thresholds = self.settings.default_health_thresholds.copy()
        
        # Apply service-specific overrides if they exist
        if service_name in self.threshold_overrides:
            for metric_name, metric_thresholds in self.threshold_overrides[service_name].items():
                if metric_name in thresholds:
                    thresholds[metric_name].update(metric_thresholds)
                else:
                    thresholds[metric_name] = metric_thresholds
        
        return thresholds
    
    def _create_alert(self, service_name: str, metric_name: str, severity: str,
                     value: float, threshold: float) -> Alert:
        """Create an alert for a service metric."""
        alert_id = f"{service_name}:{metric_name}:{severity}"
        
        message = f"Service {service_name} {metric_name} is {severity}: {value} >= {threshold}"
        if metric_name == "response_time_ms":
            message = f"Service {service_name} response time is {severity}: {value}ms >= {threshold}ms"
        elif metric_name == "error_rate_percent":
            message = f"Service {service_name} error rate is {severity}: {value}% >= {threshold}%"
        elif metric_name.endswith("_usage_percent"):
            resource = metric_name.replace("_usage_percent", "")
            message = f"Service {service_name} {resource} usage is {severity}: {value}% >= {threshold}%"
        
        return Alert(
            id=alert_id,
            service_name=service_name,
            metric_name=metric_name,
            severity=severity,
            message=message,
            value=value,
            threshold=threshold,
            timestamp=datetime.utcnow()
        )
    
    async def _process_alert(self, alert: Alert) -> None:
        """Process a new alert."""
        # Check if alert is in cooldown
        if await self._is_alert_in_cooldown(alert.id):
            logger.debug("Alert in cooldown, skipping", alert_id=alert.id)
            return
        
        async with self._alerts_lock:
            # Check if alert already exists
            if alert.id in self.active_alerts:
                # Update existing alert
                existing_alert = self.active_alerts[alert.id]
                existing_alert.value = alert.value
                existing_alert.timestamp = alert.timestamp
                logger.debug("Updated existing alert", alert_id=alert.id)
            else:
                # Add new alert
                self.active_alerts[alert.id] = alert
                self.alert_history.append(alert)
                
                logger.warning(
                    "New alert generated",
                    alert_id=alert.id,
                    service=alert.service_name,
                    metric=alert.metric_name,
                    severity=alert.severity,
                    value=alert.value,
                    threshold=alert.threshold
                )
                
                # Set cooldown
                self.alert_cooldowns[alert.id] = datetime.utcnow() + timedelta(
                    minutes=self.settings.alert_cooldown_minutes
                )
                
                # Send notifications
                await self._send_alert_notifications(alert)
                
                self.metrics.increment_counter("alerts_generated")
                self.metrics.increment_counter(f"alerts_{alert.severity}")
    
    async def _is_alert_in_cooldown(self, alert_id: str) -> bool:
        """Check if alert is in cooldown period."""
        if alert_id in self.alert_cooldowns:
            cooldown_until = self.alert_cooldowns[alert_id]
            if datetime.utcnow() < cooldown_until:
                return True
            else:
                # Cooldown expired, remove it
                del self.alert_cooldowns[alert_id]
        
        return False
    
    async def _check_resolved_alerts(self, current_health_data: Dict[str, Dict[str, Any]]) -> int:
        """Check for alerts that should be resolved."""
        resolved_count = 0
        
        async with self._alerts_lock:
            alerts_to_resolve = []
            
            for alert_id, alert in self.active_alerts.items():
                if alert.resolved:
                    continue
                
                # Check if the metric is now within threshold
                service_data = current_health_data.get(alert.service_name, {})
                current_value = service_data.get(alert.metric_name)
                
                if current_value is not None and current_value < alert.threshold:
                    alerts_to_resolve.append(alert)
            
            # Resolve alerts
            for alert in alerts_to_resolve:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                
                logger.info(
                    "Alert resolved",
                    alert_id=alert.id,
                    service=alert.service_name,
                    metric=alert.metric_name,
                    resolved_at=alert.resolved_at.isoformat()
                )
                
                await self._send_resolution_notification(alert)
                resolved_count += 1
        
        return resolved_count
    
    async def _cleanup_old_alerts(self) -> None:
        """Clean up old resolved alerts from active alerts."""
        retention_days = self.settings.alert_history_retention_days
        cutoff_time = datetime.utcnow() - timedelta(days=retention_days)
        
        async with self._alerts_lock:
            # Remove old resolved alerts from active alerts
            old_alert_ids = []
            for alert_id, alert in self.active_alerts.items():
                if (alert.resolved and 
                    alert.resolved_at and 
                    alert.resolved_at < cutoff_time):
                    old_alert_ids.append(alert_id)
            
            for alert_id in old_alert_ids:
                del self.active_alerts[alert_id]
            
            # Clean up alert history
            self.alert_history = [
                alert for alert in self.alert_history
                if alert.timestamp > cutoff_time
            ]
            
            # Clean up old cooldowns
            current_time = datetime.utcnow()
            expired_cooldowns = [
                alert_id for alert_id, cooldown_until in self.alert_cooldowns.items()
                if current_time >= cooldown_until
            ]
            for alert_id in expired_cooldowns:
                del self.alert_cooldowns[alert_id]
    
    async def _send_alert_notifications(self, alert: Alert) -> None:
        """Send alert notifications through configured channels."""
        if not self.settings.alert_notifications_enabled:
            return
        
        for channel in self.settings.notification_channels:
            try:
                if channel == "console":
                    await self._send_console_notification(alert)
                elif channel == "redis":
                    await self._send_redis_notification(alert)
                else:
                    logger.warning("Unknown notification channel", channel=channel)
            
            except Exception as e:
                logger.error(
                    "Failed to send alert notification",
                    channel=channel,
                    alert_id=alert.id,
                    error=str(e)
                )
    
    async def _send_console_notification(self, alert: Alert) -> None:
        """Send alert to console (already logged)."""
        # Alert is already logged in _process_alert, no additional action needed
        pass
    
    async def _send_redis_notification(self, alert: Alert) -> None:
        """Send alert to Redis topic."""
        if not self.redis_client:
            return
        
        try:
            alert_event = {
                "event_type": "alert_triggered",
                "alert": alert.to_dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.redis_client.publish(
                self.settings.alert_events_topic,
                json.dumps(alert_event)
            )
            
        except Exception as e:
            logger.error("Failed to publish alert to Redis", error=str(e))
    
    async def _send_resolution_notification(self, alert: Alert) -> None:
        """Send alert resolution notification."""
        if not self.settings.alert_notifications_enabled:
            return
        
        for channel in self.settings.notification_channels:
            try:
                if channel == "redis" and self.redis_client:
                    resolution_event = {
                        "event_type": "alert_resolved",
                        "alert": alert.to_dict(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    await self.redis_client.publish(
                        self.settings.alert_events_topic,
                        json.dumps(resolution_event)
                    )
            
            except Exception as e:
                logger.error("Failed to send resolution notification", error=str(e))
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active (unresolved) alerts."""
        async with self._alerts_lock:
            active_alerts = [
                alert.to_dict() for alert in self.active_alerts.values()
                if not alert.resolved
            ]
        
        # Sort by severity and timestamp
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        active_alerts.sort(
            key=lambda x: (severity_order.get(x["severity"], 3), x["timestamp"])
        )
        
        return active_alerts
    
    async def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        """Acknowledge an alert."""
        async with self._alerts_lock:
            if alert_id not in self.active_alerts:
                return {"success": False, "error": "Alert not found"}
            
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            
            logger.info("Alert acknowledged", alert_id=alert_id)
            
            return {
                "success": True,
                "alert_id": alert_id,
                "acknowledged_at": datetime.utcnow().isoformat()
            }
    
    async def resolve_alert(self, alert_id: str) -> Dict[str, Any]:
        """Manually resolve an alert."""
        async with self._alerts_lock:
            if alert_id not in self.active_alerts:
                return {"success": False, "error": "Alert not found"}
            
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            
            logger.info("Alert manually resolved", alert_id=alert_id)
            
            await self._send_resolution_notification(alert)
            
            return {
                "success": True,
                "alert_id": alert_id,
                "resolved_at": alert.resolved_at.isoformat()
            }
    
    async def update_threshold(self, service_name: str, metric_name: str,
                             threshold_type: str, threshold_value: float) -> Dict[str, Any]:
        """Update health threshold for a service metric."""
        if threshold_type not in ["critical", "warning", "info"]:
            return {
                "success": False,
                "error": f"Invalid threshold type: {threshold_type}"
            }
        
        # Initialize service overrides if not exists
        if service_name not in self.threshold_overrides:
            self.threshold_overrides[service_name] = {}
        
        if metric_name not in self.threshold_overrides[service_name]:
            self.threshold_overrides[service_name][metric_name] = {}
        
        # Update threshold
        self.threshold_overrides[service_name][metric_name][threshold_type] = threshold_value
        
        logger.info(
            "Threshold updated",
            service=service_name,
            metric=metric_name,
            threshold_type=threshold_type,
            threshold_value=threshold_value
        )
        
        return {
            "success": True,
            "service_name": service_name,
            "metric_name": metric_name,
            "threshold_type": threshold_type,
            "threshold_value": threshold_value,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    async def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        async with self._alerts_lock:
            total_alerts = len(self.alert_history)
            active_alerts = len([a for a in self.active_alerts.values() if not a.resolved])
            resolved_alerts = len([a for a in self.active_alerts.values() if a.resolved])
            
            # Count by severity
            severity_counts = {"critical": 0, "warning": 0, "info": 0}
            for alert in self.alert_history:
                if alert.severity in severity_counts:
                    severity_counts[alert.severity] += 1
            
            # Count by service
            service_counts = {}
            for alert in self.alert_history:
                service_counts[alert.service_name] = service_counts.get(alert.service_name, 0) + 1
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "resolved_alerts": resolved_alerts,
            "alerts_in_cooldown": len(self.alert_cooldowns),
            "severity_breakdown": severity_counts,
            "service_breakdown": service_counts,
            "threshold_overrides": len(self.threshold_overrides)
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get alert manager status."""
        async with self._alerts_lock:
            active_count = len([a for a in self.active_alerts.values() if not a.resolved])
        
        return {
            "running": self.running,
            "active_alerts": active_count,
            "total_alerts_in_history": len(self.alert_history),
            "cooldowns_active": len(self.alert_cooldowns),
            "notifications_enabled": self.settings.alert_notifications_enabled,
            "notification_channels": self.settings.notification_channels,
            "cooldown_minutes": self.settings.alert_cooldown_minutes
        }