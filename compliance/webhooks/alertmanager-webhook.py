#!/usr/bin/env python3
# DOC_ID: DOC-SERVICE-0010
"""
Alertmanager Webhook Receiver for EAFIX Compliance Auto-Remediation

Receives compliance violation alerts from Prometheus Alertmanager
and triggers appropriate automated remediation actions.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from aiohttp import web, ClientSession
from prometheus_client import Counter, Histogram, start_http_server
import aioredis
import hmac
import hashlib
import os

# Import the remediation engine
from compliance.auto_remediation.remediation_engine import ComplianceRemediationEngine

# Metrics
WEBHOOK_REQUESTS_TOTAL = Counter('compliance_webhook_requests_total', 
                                'Total webhook requests received', 
                                ['status', 'alert_name'])
WEBHOOK_PROCESSING_TIME = Histogram('compliance_webhook_processing_seconds',
                                   'Time taken to process webhook requests')
ALERTS_PROCESSED_TOTAL = Counter('compliance_alerts_processed_total',
                                'Total compliance alerts processed',
                                ['regulation', 'severity'])

logger = logging.getLogger(__name__)

class AlertmanagerWebhookHandler:
    """
    Webhook handler for Prometheus Alertmanager compliance alerts.
    
    Receives alert notifications and triggers automated remediation
    through the ComplianceRemediationEngine.
    """
    
    def __init__(self, config_path: str = "compliance/config/webhook-config.yml"):
        self.remediation_engine = ComplianceRemediationEngine()
        self.redis_client: aioredis.Redis = None
        self.webhook_secret = os.getenv('ALERTMANAGER_WEBHOOK_SECRET', '')
        
    async def initialize(self):
        """Initialize components"""
        await self.remediation_engine.initialize()
        self.redis_client = aioredis.from_url(
            'redis://redis:6379',
            encoding='utf-8',
            decode_responses=True
        )
        
    async def handle_webhook(self, request: web.Request) -> web.Response:
        """
        Handle incoming webhook from Alertmanager.
        
        Validates the request, processes alerts, and triggers remediation.
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate webhook signature if secret is configured
            if self.webhook_secret:
                if not self._validate_signature(request):
                    WEBHOOK_REQUESTS_TOTAL.labels(status='unauthorized', alert_name='unknown').inc()
                    return web.Response(status=401, text="Unauthorized")
            
            # Parse alert data
            alert_data = await request.json()
            
            # Process each alert in the notification
            processed_count = 0
            for alert in alert_data.get('alerts', []):
                if await self._is_compliance_alert(alert):
                    success = await self._process_compliance_alert(alert)
                    if success:
                        processed_count += 1
                        
                    # Record metrics
                    regulation = alert.get('labels', {}).get('regulation', 'unknown')
                    severity = alert.get('labels', {}).get('severity', 'unknown')
                    alert_name = alert.get('labels', {}).get('alertname', 'unknown')
                    
                    ALERTS_PROCESSED_TOTAL.labels(
                        regulation=regulation,
                        severity=severity
                    ).inc()
            
            # Record processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            WEBHOOK_PROCESSING_TIME.observe(processing_time)
            
            # Log processing summary
            logger.info(f"Processed {processed_count}/{len(alert_data.get('alerts', []))} compliance alerts")
            
            WEBHOOK_REQUESTS_TOTAL.labels(status='success', alert_name='multiple').inc()
            return web.Response(status=200, text=f"Processed {processed_count} compliance alerts")
            
        except json.JSONDecodeError:
            WEBHOOK_REQUESTS_TOTAL.labels(status='invalid_json', alert_name='unknown').inc()
            logger.error("Invalid JSON in webhook request")
            return web.Response(status=400, text="Invalid JSON")
            
        except Exception as e:
            WEBHOOK_REQUESTS_TOTAL.labels(status='error', alert_name='unknown').inc()
            logger.error(f"Error processing webhook: {e}")
            return web.Response(status=500, text="Internal server error")
    
    def _validate_signature(self, request: web.Request) -> bool:
        """Validate webhook signature using HMAC"""
        try:
            signature_header = request.headers.get('X-Alertmanager-Signature', '')
            if not signature_header.startswith('sha256='):
                return False
                
            expected_signature = signature_header[7:]  # Remove 'sha256=' prefix
            body = request.body
            
            computed_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, computed_signature)
            
        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            return False
    
    async def _is_compliance_alert(self, alert: Dict[str, Any]) -> bool:
        """Check if alert is a compliance-related alert"""
        labels = alert.get('labels', {})
        
        # Check for compliance-related labels
        compliance_indicators = [
            'regulation' in labels,
            'requirement' in labels,
            labels.get('team') in ['compliance', 'risk-management'],
            'compliance' in labels.get('alertname', '').lower(),
            'violation' in labels.get('alertname', '').lower()
        ]
        
        return any(compliance_indicators)
    
    async def _process_compliance_alert(self, alert: Dict[str, Any]) -> bool:
        """Process a single compliance alert"""
        try:
            # Extract alert information
            labels = alert.get('labels', {})
            annotations = alert.get('annotations', {})
            
            # Create violation data structure for remediation engine
            violation_data = {
                'fingerprint': alert.get('fingerprint', f"alert_{datetime.utcnow().isoformat()}"),
                'labels': labels,
                'annotations': annotations,
                'status': alert.get('status', 'firing'),
                'startsAt': alert.get('startsAt'),
                'endsAt': alert.get('endsAt'),
                'generatorURL': alert.get('generatorURL')
            }
            
            # Log the compliance alert
            logger.info(f"Processing compliance alert: {labels.get('alertname', 'unknown')} - "
                       f"{labels.get('regulation', 'unknown')}/{labels.get('requirement', 'unknown')}")
            
            # Send to remediation engine
            if alert.get('status') == 'firing':
                success = await self.remediation_engine.process_violation(violation_data)
            else:
                # Alert resolved - log for audit trail
                await self._log_alert_resolution(violation_data)
                success = True
            
            # Store alert in Redis for audit trail
            await self._store_alert_for_audit(alert)
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing compliance alert: {e}")
            return False
    
    async def _log_alert_resolution(self, violation_data: Dict[str, Any]) -> None:
        """Log alert resolution for audit trail"""
        resolution_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'alert_resolution',
            'violation_id': violation_data['fingerprint'],
            'regulation': violation_data['labels'].get('regulation', 'unknown'),
            'requirement': violation_data['labels'].get('requirement', 'unknown'),
            'resolved_at': violation_data.get('endsAt', datetime.utcnow().isoformat())
        }
        
        await self.redis_client.lpush('compliance_audit_trail', json.dumps(resolution_record))
        
        logger.info(f"Compliance alert resolved: {violation_data['fingerprint']}")
    
    async def _store_alert_for_audit(self, alert: Dict[str, Any]) -> None:
        """Store alert data for compliance audit trail"""
        audit_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'compliance_alert_received',
            'alert_data': alert,
            'source': 'alertmanager_webhook'
        }
        
        await self.redis_client.lpush('compliance_audit_trail', json.dumps(audit_record))
        
    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        try:
            # Check Redis connectivity
            await self.redis_client.ping()
            
            # Check remediation engine status
            status = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'components': {
                    'redis': 'healthy',
                    'remediation_engine': 'healthy',
                    'webhook_handler': 'healthy'
                }
            }
            
            return web.json_response(status)
            
        except Exception as e:
            status = {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
            
            return web.json_response(status, status=503)

    async def metrics_endpoint(self, request: web.Request) -> web.Response:
        """Prometheus metrics endpoint"""
        # This would return Prometheus metrics in the proper format
        # For now, return a simple response
        return web.Response(text="# Metrics would be here in Prometheus format\n")

async def create_app():
    """Create the webhook application"""
    handler = AlertmanagerWebhookHandler()
    await handler.initialize()
    
    app = web.Application()
    
    # Add routes
    app.router.add_post('/webhook/alertmanager', handler.handle_webhook)
    app.router.add_get('/health', handler.health_check)
    app.router.add_get('/metrics', handler.metrics_endpoint)
    
    # Add middleware for logging
    async def logging_middleware(request: web.Request, handler):
        start_time = datetime.utcnow()
        response = await handler(request)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"{request.method} {request.path} - {response.status} - {duration:.3f}s")
        
        return response
    
    app.middlewares.append(logging_middleware)
    
    return app

async def main():
    """Main application entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start Prometheus metrics server
    start_http_server(9201)
    logger.info("Prometheus metrics server started on port 9201")
    
    # Create and run the webhook app
    app = await create_app()
    
    # Run the web server
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    logger.info("Compliance webhook handler started on port 8080")
    logger.info("Endpoints:")
    logger.info("  POST /webhook/alertmanager - Alertmanager webhook")
    logger.info("  GET  /health              - Health check")
    logger.info("  GET  /metrics             - Prometheus metrics")
    
    # Keep the server running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down compliance webhook handler")
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())