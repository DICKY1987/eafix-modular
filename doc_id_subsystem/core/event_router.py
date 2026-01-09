# DOC_ID: DOC-SCRIPT-1006
"""
Event Router for Doc ID System
Provides centralized event routing and dispatching
"""
import logging
from typing import Dict, List, Callable, Any, Optional
from event_emitter import AsyncEventEmitter

logger = logging.getLogger(__name__)


class EventRouter:
    """Routes events between components in the doc_id system"""
    
    def __init__(self, sinks: Optional[List[Any]] = None):
        """
        Initialize EventRouter.
        
        Args:
            sinks: Optional list of event sinks (for test compatibility)
        """
        self.emitter = AsyncEventEmitter()
        self.routes: Dict[str, List[Callable]] = {}
        self.sinks = sinks or []
        
    def register_route(self, event_type: str, handler: Callable):
        """Register a handler for an event type"""
        if event_type not in self.routes:
            self.routes[event_type] = []
        self.routes[event_type].append(handler)
        logger.debug(f"Registered route for {event_type}")
        
    def emit(self, event_type: str, data: Any = None):
        """Emit an event to all registered handlers"""
        self.emitter.emit(event_type, data)
        if event_type in self.routes:
            for handler in self.routes[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")
                    
    def remove_route(self, event_type: str, handler: Callable):
        """Remove a handler for an event type"""
        if event_type in self.routes:
            try:
                self.routes[event_type].remove(handler)
                logger.debug(f"Removed route for {event_type}")
            except ValueError:
                pass
                
    def clear_routes(self, event_type: str = None):
        """Clear all routes for an event type, or all routes if None"""
        if event_type:
            self.routes[event_type] = []
        else:
            self.routes.clear()
