"""WebSocket connection management for real-time communication."""

import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from fastapi import WebSocket, WebSocketDisconnect
import redis
import uuid

logger = logging.getLogger(__name__)

@dataclass
class Connection:
    """Represents a WebSocket connection."""
    websocket: WebSocket
    client_id: str
    user_id: Optional[str] = None
    subscriptions: Set[str] = None
    
    def __post_init__(self):
        if self.subscriptions is None:
            self.subscriptions = set()

class ConnectionManager:
    """Manages WebSocket connections and message routing."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.connections: Dict[str, Connection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of client_ids
        self.subscription_map: Dict[str, Set[str]] = {}  # topic -> set of client_ids
        self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        
    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> str:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        client_id = str(uuid.uuid4())
        connection = Connection(
            websocket=websocket,
            client_id=client_id,
            user_id=user_id
        )
        
        self.connections[client_id] = connection
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(client_id)
            
        logger.info(f"Client {client_id} connected (user: {user_id})")
        
        # Send welcome message
        await self.send_to_connection(client_id, {
            "type": "connection.established",
            "client_id": client_id,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        return client_id
    
    async def disconnect(self, client_id: str):
        """Remove a WebSocket connection."""
        if client_id not in self.connections:
            return
            
        connection = self.connections[client_id]
        
        # Remove from user connections
        if connection.user_id and connection.user_id in self.user_connections:
            self.user_connections[connection.user_id].discard(client_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]
        
        # Remove from subscriptions
        for topic in connection.subscriptions:
            if topic in self.subscription_map:
                self.subscription_map[topic].discard(client_id)
                if not self.subscription_map[topic]:
                    del self.subscription_map[topic]
        
        del self.connections[client_id]
        logger.info(f"Client {client_id} disconnected")
    
    async def subscribe(self, client_id: str, topics: List[str]):
        """Subscribe a connection to topics."""
        if client_id not in self.connections:
            return False
            
        connection = self.connections[client_id]
        
        for topic in topics:
            connection.subscriptions.add(topic)
            if topic not in self.subscription_map:
                self.subscription_map[topic] = set()
            self.subscription_map[topic].add(client_id)
            
        logger.info(f"Client {client_id} subscribed to: {topics}")
        return True
    
    async def unsubscribe(self, client_id: str, topics: List[str]):
        """Unsubscribe a connection from topics."""
        if client_id not in self.connections:
            return False
            
        connection = self.connections[client_id]
        
        for topic in topics:
            connection.subscriptions.discard(topic)
            if topic in self.subscription_map:
                self.subscription_map[topic].discard(client_id)
                if not self.subscription_map[topic]:
                    del self.subscription_map[topic]
                    
        logger.info(f"Client {client_id} unsubscribed from: {topics}")
        return True
    
    async def send_to_connection(self, client_id: str, message: Dict[str, Any]) -> bool:
        """Send message to a specific connection."""
        if client_id not in self.connections:
            return False
            
        try:
            await self.connections[client_id].websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {client_id}: {e}")
            await self.disconnect(client_id)
            return False
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """Send message to all connections for a user."""
        if user_id not in self.user_connections:
            return 0
            
        sent_count = 0
        client_ids = list(self.user_connections[user_id])  # Copy to avoid modification during iteration
        
        for client_id in client_ids:
            if await self.send_to_connection(client_id, message):
                sent_count += 1
                
        return sent_count
    
    async def broadcast_to_topic(self, topic: str, message: Dict[str, Any]) -> int:
        """Broadcast message to all subscribers of a topic."""
        if topic not in self.subscription_map:
            return 0
            
        sent_count = 0
        client_ids = list(self.subscription_map[topic])  # Copy to avoid modification during iteration
        
        for client_id in client_ids:
            if await self.send_to_connection(client_id, message):
                sent_count += 1
                
        return sent_count
    
    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """Broadcast message to all connected clients."""
        sent_count = 0
        client_ids = list(self.connections.keys())  # Copy to avoid modification during iteration
        
        for client_id in client_ids:
            if await self.send_to_connection(client_id, message):
                sent_count += 1
                
        return sent_count
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": len(self.connections),
            "unique_users": len(self.user_connections),
            "topics": len(self.subscription_map),
            "connections_by_topic": {
                topic: len(clients) for topic, clients in self.subscription_map.items()
            }
        }
    
    async def handle_client_message(self, client_id: str, message: str):
        """Handle incoming message from client."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                topics = data.get("topics", [])
                await self.subscribe(client_id, topics)
                await self.send_to_connection(client_id, {
                    "type": "subscription.confirmed",
                    "topics": topics
                })
                
            elif message_type == "unsubscribe":
                topics = data.get("topics", [])
                await self.unsubscribe(client_id, topics)
                await self.send_to_connection(client_id, {
                    "type": "unsubscription.confirmed",
                    "topics": topics
                })
                
            elif message_type == "ping":
                await self.send_to_connection(client_id, {"type": "pong"})
                
            else:
                logger.warning(f"Unknown message type from {client_id}: {message_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from {client_id}: {e}")
            await self.send_to_connection(client_id, {
                "type": "error",
                "message": "Invalid JSON format"
            })
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
            await self.send_to_connection(client_id, {
                "type": "error",
                "message": "Internal server error"
            })

# Global connection manager instance
connection_manager = ConnectionManager()