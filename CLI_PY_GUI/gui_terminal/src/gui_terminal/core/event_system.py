"""
Event System Implementation
WebSocket integration and platform event handling
"""

import json
import time
import asyncio
import logging
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
    PYQT_VERSION = 6
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSignal, QThread, QTimer
    PYQT_VERSION = 5

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for platform integration"""
    TERMINAL_START = "terminal_start"
    TERMINAL_STOP = "terminal_stop"
    COMMAND_EXECUTED = "command_executed"
    OUTPUT_RECEIVED = "output_received"
    ERROR_OCCURRED = "error_occurred"
    WORKFLOW_UPDATE = "workflow_update"
    COST_UPDATE = "cost_update"
    SECURITY_VIOLATION = "security_violation"
    SESSION_INFO = "session_info"


@dataclass
class TerminalEvent:
    """Terminal event data structure"""
    event_type: EventType
    timestamp: float
    session_id: str
    user_id: str = "default"
    data: Dict[str, Any] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        result = asdict(self)
        result['event_type'] = self.event_type.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TerminalEvent':
        """Create event from dictionary"""
        event_type = EventType(data['event_type'])
        return cls(
            event_type=event_type,
            timestamp=data['timestamp'],
            session_id=data['session_id'],
            user_id=data.get('user_id', 'default'),
            data=data.get('data', {})
        )


class WebSocketClient(QThread):
    """WebSocket client for platform communication"""

    connected = pyqtSignal()
    disconnected = pyqtSignal()
    event_received = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, url: str, auth_token: Optional[str] = None):
        super().__init__()
        self.url = url
        self.auth_token = auth_token
        self.websocket = None
        self.should_stop = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds

    def run(self):
        """Main WebSocket client loop"""
        if not WEBSOCKETS_AVAILABLE:
            self.error_occurred.emit("websockets library not available")
            return

        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()

        try:
            loop.run_until_complete(self._connect_and_listen())
        except Exception as e:
            logger.error(f"WebSocket client error: {e}")
            self.error_occurred.emit(str(e))
        finally:
            loop.close()

    async def _connect_and_listen(self):
        """Connect to WebSocket and listen for events"""
        while not self.should_stop and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                # Prepare headers
                headers = {}
                if self.auth_token:
                    headers['Authorization'] = f"Bearer {self.auth_token}"

                # Connect to WebSocket
                logger.info(f"Connecting to WebSocket: {self.url}")
                self.websocket = await websockets.connect(self.url, extra_headers=headers)

                self.connected.emit()
                self.reconnect_attempts = 0
                logger.info("WebSocket connected successfully")

                # Listen for messages
                async for message in self.websocket:
                    try:
                        data = json.loads(message)
                        self.event_received.emit(data)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON received: {e}")

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                self.disconnected.emit()
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                self.error_occurred.emit(str(e))

            # Reconnect logic
            if not self.should_stop and self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                logger.info(f"Reconnecting in {self.reconnect_delay} seconds (attempt {self.reconnect_attempts})")
                await asyncio.sleep(self.reconnect_delay)

        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.error_occurred.emit("Max reconnection attempts reached")

    async def _send_message(self, message: Dict[str, Any]):
        """Send message through WebSocket"""
        if self.websocket and not self.websocket.closed:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message: {e}")

    def send_event(self, event: TerminalEvent):
        """Send event to platform"""
        if self.websocket:
            message = {
                'type': 'terminal_event',
                'event': event.to_dict()
            }
            # Schedule message sending in the event loop
            asyncio.run_coroutine_threadsafe(
                self._send_message(message),
                self.thread().eventLoop() if hasattr(self.thread(), 'eventLoop') else asyncio.get_event_loop()
            )

    def stop(self):
        """Stop WebSocket client"""
        self.should_stop = True
        if self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.websocket.close(),
                self.thread().eventLoop() if hasattr(self.thread(), 'eventLoop') else asyncio.get_event_loop()
            )


class EventBuffer:
    """Event buffer for offline storage"""

    def __init__(self, max_size: int = 1000):
        self.events = []
        self.max_size = max_size

    def add_event(self, event: TerminalEvent):
        """Add event to buffer"""
        self.events.append(event)
        if len(self.events) > self.max_size:
            self.events.pop(0)  # Remove oldest event

    def get_events(self, count: Optional[int] = None) -> List[TerminalEvent]:
        """Get events from buffer"""
        if count is None:
            return self.events.copy()
        return self.events[-count:] if count > 0 else []

    def clear(self):
        """Clear event buffer"""
        self.events.clear()

    def size(self) -> int:
        """Get buffer size"""
        return len(self.events)


class EventSystem(QObject):
    """
    Local event system for terminal events
    """

    event_emitted = pyqtSignal(TerminalEvent)

    def __init__(self):
        super().__init__()
        self.subscribers = {}  # event_type -> list of callbacks
        self.event_buffer = EventBuffer()

    def subscribe(self, event_type: EventType, callback: Callable[[TerminalEvent], None]):
        """Subscribe to event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable[[TerminalEvent], None]):
        """Unsubscribe from event type"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
            except ValueError:
                pass

    def emit_event(self, event: TerminalEvent):
        """Emit event to subscribers"""
        # Store in buffer
        self.event_buffer.add_event(event)

        # Notify subscribers
        if event.event_type in self.subscribers:
            for callback in self.subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback: {e}")

        # Emit Qt signal
        self.event_emitted.emit(event)

    def get_recent_events(self, count: int = 10) -> List[TerminalEvent]:
        """Get recent events"""
        return self.event_buffer.get_events(count)


class PlatformEventIntegration(QObject):
    """
    Integration with CLI Multi-Rapid platform event system
    """

    connection_status_changed = pyqtSignal(bool)
    platform_event_received = pyqtSignal(dict)

    def __init__(self, websocket_url: str, auth_token: Optional[str] = None):
        super().__init__()
        self.websocket_url = websocket_url
        self.auth_token = auth_token

        # Components
        self.local_event_system = EventSystem()
        self.websocket_client = None
        self.connected = False

        # Setup
        self.setup_local_subscriptions()

    def setup_local_subscriptions(self):
        """Setup local event subscriptions"""
        # Subscribe to all events for platform forwarding
        for event_type in EventType:
            self.local_event_system.subscribe(event_type, self._forward_event_to_platform)

    def connect_to_platform(self):
        """Connect to platform WebSocket"""
        if self.websocket_client and self.websocket_client.isRunning():
            return

        self.websocket_client = WebSocketClient(self.websocket_url, self.auth_token)

        # Connect signals
        self.websocket_client.connected.connect(self._on_connected)
        self.websocket_client.disconnected.connect(self._on_disconnected)
        self.websocket_client.event_received.connect(self._on_platform_event)
        self.websocket_client.error_occurred.connect(self._on_error)

        self.websocket_client.start()
        logger.info("Connecting to platform...")

    def disconnect_from_platform(self):
        """Disconnect from platform WebSocket"""
        if self.websocket_client:
            self.websocket_client.stop()
            self.websocket_client.wait()
            self.websocket_client = None
        self.connected = False
        self.connection_status_changed.emit(False)

    def emit_terminal_event(self, event_type: EventType, session_id: str,
                          user_id: str = "default", data: Optional[Dict[str, Any]] = None):
        """Emit terminal event"""
        event = TerminalEvent(
            event_type=event_type,
            timestamp=time.time(),
            session_id=session_id,
            user_id=user_id,
            data=data or {}
        )
        self.local_event_system.emit_event(event)

    def _forward_event_to_platform(self, event: TerminalEvent):
        """Forward local event to platform"""
        if self.connected and self.websocket_client:
            self.websocket_client.send_event(event)

    def _on_connected(self):
        """Handle WebSocket connection"""
        self.connected = True
        self.connection_status_changed.emit(True)
        logger.info("Platform connection established")

    def _on_disconnected(self):
        """Handle WebSocket disconnection"""
        self.connected = False
        self.connection_status_changed.emit(False)
        logger.info("Platform connection lost")

    def _on_platform_event(self, data: Dict[str, Any]):
        """Handle event from platform"""
        self.platform_event_received.emit(data)
        logger.debug(f"Platform event received: {data.get('type', 'unknown')}")

    def _on_error(self, error_message: str):
        """Handle WebSocket error"""
        logger.error(f"Platform connection error: {error_message}")

    def handle_workflow_event(self, event: Dict[str, Any]):
        """Handle workflow status updates from platform"""
        event_type = event.get('type')
        data = event.get('data', {})

        if event_type == 'workflow_started':
            logger.info(f"Workflow started: {data.get('workflow_id')}")
        elif event_type == 'workflow_completed':
            logger.info(f"Workflow completed: {data.get('workflow_id')}")
        elif event_type == 'workflow_failed':
            logger.warning(f"Workflow failed: {data.get('workflow_id')}")

        # Emit local event
        self.emit_terminal_event(
            EventType.WORKFLOW_UPDATE,
            session_id="platform",
            data=data
        )

    def handle_cost_update(self, cost_data: Dict[str, Any]):
        """Handle cost tracking updates from platform"""
        logger.info(f"Cost update: ${cost_data.get('current_cost', 0):.4f}")

        # Emit local event
        self.emit_terminal_event(
            EventType.COST_UPDATE,
            session_id="platform",
            data=cost_data
        )

    def get_connection_status(self) -> Dict[str, Any]:
        """Get connection status information"""
        return {
            "connected": self.connected,
            "websocket_url": self.websocket_url,
            "reconnect_attempts": self.websocket_client.reconnect_attempts if self.websocket_client else 0,
            "events_buffered": self.local_event_system.event_buffer.size()
        }

    def get_recent_events(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent events as dictionaries"""
        events = self.local_event_system.get_recent_events(count)
        return [event.to_dict() for event in events]