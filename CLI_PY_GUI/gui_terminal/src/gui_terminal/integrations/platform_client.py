"""
Platform Client
Integration with CLI Multi-Rapid platform services
"""

import json
import time
import logging
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer
    PYQT_VERSION = 6
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSignal, QTimer
    PYQT_VERSION = 5

logger = logging.getLogger(__name__)


@dataclass
class PlatformConfig:
    """Platform configuration"""
    base_url: str
    api_key: str
    websocket_url: str
    timeout: int = 30
    retry_attempts: int = 3


class PlatformClient(QObject):
    """
    Client for CLI Multi-Rapid platform integration
    """

    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error_occurred = pyqtSignal(str)
    workflow_updated = pyqtSignal(dict)
    cost_updated = pyqtSignal(dict)

    def __init__(self, config: PlatformConfig):
        super().__init__()
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'GUI-Terminal/1.0.0'
        })

        # Health check timer
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self.health_check)
        self.health_timer.start(60000)  # Check every minute

    def health_check(self):
        """Perform platform health check"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/status",
                timeout=5
            )
            if response.status_code == 200:
                if not hasattr(self, '_was_connected') or not self._was_connected:
                    self.connected.emit()
                    self._was_connected = True
            else:
                self._handle_disconnect()
        except Exception as e:
            self._handle_disconnect()
            logger.debug(f"Health check failed: {e}")

    def _handle_disconnect(self):
        """Handle platform disconnection"""
        if hasattr(self, '_was_connected') and self._was_connected:
            self.disconnected.emit()
            self._was_connected = False

    def execute_task(self, description: str, max_cost: Optional[float] = None,
                    force_agent: Optional[str] = None) -> Dict[str, Any]:
        """Execute task via platform API"""
        try:
            data = {
                'description': description,
                'source': 'gui_terminal',
                'timestamp': time.time()
            }

            if max_cost is not None:
                data['max_cost'] = max_cost
            if force_agent:
                data['force_agent'] = force_agent

            response = self.session.post(
                f"{self.config.base_url}/execute-task",
                json=data,
                timeout=self.config.timeout
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Task executed successfully: {result.get('task_id')}")
                return result
            else:
                error_msg = f"Task execution failed: {response.status_code}"
                self.error_occurred.emit(error_msg)
                return {'success': False, 'error': error_msg}

        except Exception as e:
            error_msg = f"Task execution error: {e}"
            self.error_occurred.emit(error_msg)
            return {'success': False, 'error': error_msg}

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/workflow/{workflow_id}/status",
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {'status': 'unknown', 'error': f'HTTP {response.status_code}'}

        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            return {'status': 'error', 'error': str(e)}

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary from platform"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/cost-tracking/summary",
                timeout=10
            )

            if response.status_code == 200:
                cost_data = response.json()
                self.cost_updated.emit(cost_data)
                return cost_data
            else:
                return {'error': f'HTTP {response.status_code}'}

        except Exception as e:
            logger.error(f"Failed to get cost summary: {e}")
            return {'error': str(e)}

    def get_system_status(self) -> Dict[str, Any]:
        """Get platform system status"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/status",
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {'status': 'unavailable', 'error': f'HTTP {response.status_code}'}

        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {'status': 'error', 'error': str(e)}

    def submit_feedback(self, feedback: Dict[str, Any]) -> bool:
        """Submit feedback to platform"""
        try:
            feedback.update({
                'source': 'gui_terminal',
                'timestamp': time.time()
            })

            response = self.session.post(
                f"{self.config.base_url}/feedback",
                json=feedback,
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Failed to submit feedback: {e}")
            return False

    def get_enterprise_integrations(self) -> Dict[str, Any]:
        """Get available enterprise integrations"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/integrations/status",
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {'integrations': {}, 'error': f'HTTP {response.status_code}'}

        except Exception as e:
            logger.error(f"Failed to get integrations: {e}")
            return {'integrations': {}, 'error': str(e)}