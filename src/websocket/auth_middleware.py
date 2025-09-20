"""WebSocket authentication middleware."""

import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import jwt
import redis
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WebSocketAuthMiddleware:
    """Authentication middleware for WebSocket connections."""
    
    def __init__(self, secret_key: str = "your-secret-key", redis_url: str = "redis://localhost:6379"):
        self.secret_key = secret_key
        # Best-effort Redis; fall back to in-memory stores when unavailable
        self.redis_client = None
        try:
            client = redis.Redis.from_url(redis_url, decode_responses=True)
            client.ping()
            self.redis_client = client
        except Exception as e:
            logger.warning(f"Redis unavailable for AuthMiddleware, using in-memory stores: {e}")
        self.algorithm = "HS256"
        # In-memory fallbacks
        self._api_keys: Dict[str, Any] = {}
        self._sessions: Dict[str, Any] = {}
        self._blacklist: set[str] = set()
        
    async def authenticate_token(self, token: Optional[str]) -> Optional[Dict[str, Any]]:
        """Authenticate JWT token and return user info."""
        if not token:
            return None
            
        try:
            # Remove Bearer prefix if present
            if token.startswith("Bearer "):
                token = token[7:]
                
            # Decode JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                logger.warning("Token expired")
                return None
            
            # Check if token is blacklisted
            token_hash = hash(token)
            try:
                if self.redis_client is not None and self.redis_client.get(f"blacklist:{token_hash}"):
                    logger.warning("Token is blacklisted")
                    return None
            except Exception as e:
                logger.warning(f"Redis blacklist check failed, falling back to memory: {e}")
                self.redis_client = None
            if token in self._blacklist:
                logger.warning("Token is blacklisted (memory)")
                return None
                
            return {
                "user_id": payload.get("user_id"),
                "username": payload.get("username"),
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", [])
            }
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token authentication error: {e}")
            return None
    
    async def authenticate_api_key(self, api_key: Optional[str]) -> Optional[Dict[str, Any]]:
        """Authenticate API key and return user info."""
        if not api_key:
            return None
            
        try:
            import json
            user_info: Optional[Dict[str, Any]] = None
            try:
                if self.redis_client is not None:
                    key_data = self.redis_client.get(f"api_key:{api_key}")
                    if key_data:
                        user_info = json.loads(key_data)
            except Exception as e:
                logger.warning(f"Redis API key check failed, falling back to memory: {e}")
                self.redis_client = None
            if user_info is None:
                user_info = self._api_keys.get(api_key)
            if not user_info:
                logger.warning("Invalid API key")
                return None
            
            # Check if API key is active
            if not user_info.get("active", False):
                logger.warning("API key is inactive")
                return None
                
            # Update last used timestamp
            user_info["last_used"] = datetime.utcnow().isoformat()
            try:
                if self.redis_client is not None:
                    self.redis_client.set(f"api_key:{api_key}", json.dumps(user_info))
                else:
                    self._api_keys[api_key] = user_info
            except Exception as e:
                logger.warning(f"Redis API key update failed, storing in memory: {e}")
                self.redis_client = None
                self._api_keys[api_key] = user_info
            
            return user_info
            
        except Exception as e:
            logger.error(f"API key authentication error: {e}")
            return None
    
    async def authenticate_session(self, session_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Authenticate session ID and return user info."""
        if not session_id:
            return None
            
        try:
            import json
            session_info: Optional[Dict[str, Any]] = None
            try:
                if self.redis_client is not None:
                    session_data = self.redis_client.get(f"session:{session_id}")
                    if session_data:
                        session_info = json.loads(session_data)
            except Exception as e:
                logger.warning(f"Redis session check failed, falling back to memory: {e}")
                self.redis_client = None
            if session_info is None:
                session_info = self._sessions.get(session_id)
            if not session_info:
                logger.warning("Invalid session")
                return None
            
            # Check session expiration
            expires_at = datetime.fromisoformat(session_info.get("expires_at", ""))
            if expires_at < datetime.utcnow():
                logger.warning("Session expired")
                self.redis_client.delete(f"session:{session_id}")
                return None
                
            # Update last activity
            session_info["last_activity"] = datetime.utcnow().isoformat()
            
            # Extend session TTL
            ttl_seconds = int((expires_at - datetime.utcnow()).total_seconds())
            try:
                if self.redis_client is not None:
                    self.redis_client.setex(f"session:{session_id}", ttl_seconds, json.dumps(session_info))
                else:
                    self._sessions[session_id] = session_info
            except Exception as e:
                logger.warning(f"Redis session update failed, storing in memory: {e}")
                self.redis_client = None
                self._sessions[session_id] = session_info
            
            return session_info.get("user_info", {})
            
        except Exception as e:
            logger.error(f"Session authentication error: {e}")
            return None
    
    async def authenticate_websocket(self, token: Optional[str] = None, api_key: Optional[str] = None, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Authenticate WebSocket connection using multiple methods."""
        # Try JWT token first
        if token:
            user_info = await self.authenticate_token(token)
            if user_info:
                return user_info
        
        # Try API key
        if api_key:
            user_info = await self.authenticate_api_key(api_key)
            if user_info:
                return user_info
        
        # Try session ID
        if session_id:
            user_info = await self.authenticate_session(session_id)
            if user_info:
                return user_info
        
        return None
    
    def generate_token(self, user_id: str, username: str, roles: list = None, permissions: list = None, expires_in_hours: int = 24) -> str:
        """Generate JWT token for user."""
        payload = {
            "user_id": user_id,
            "username": username,
            "roles": roles or [],
            "permissions": permissions or [],
            "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    async def create_api_key(self, user_id: str, username: str, roles: list = None, permissions: list = None, expires_in_days: int = 365) -> str:
        """Create API key for user."""
        import secrets
        api_key = secrets.token_urlsafe(32)
        
        key_data = {
            "user_id": user_id,
            "username": username,
            "roles": roles or [],
            "permissions": permissions or [],
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat(),
            "active": True,
            "last_used": None
        }
        
        import json
        ttl_seconds = expires_in_days * 24 * 60 * 60
        try:
            if self.redis_client is not None:
                self.redis_client.setex(f"api_key:{api_key}", ttl_seconds, json.dumps(key_data))
            else:
                self._api_keys[api_key] = key_data
        except Exception as e:
            logger.warning(f"Redis API key create failed, storing in memory: {e}")
            self.redis_client = None
            self._api_keys[api_key] = key_data
        
        return api_key
    
    async def create_session(self, user_id: str, username: str, roles: list = None, permissions: list = None, expires_in_hours: int = 8) -> str:
        """Create session for user."""
        import secrets
        session_id = secrets.token_urlsafe(32)
        
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        session_data = {
            "user_info": {
                "user_id": user_id,
                "username": username,
                "roles": roles or [],
                "permissions": permissions or []
            },
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        import json
        ttl_seconds = expires_in_hours * 60 * 60
        try:
            if self.redis_client is not None:
                self.redis_client.setex(f"session:{session_id}", ttl_seconds, json.dumps(session_data))
            else:
                self._sessions[session_id] = session_data
        except Exception as e:
            logger.warning(f"Redis session create failed, storing in memory: {e}")
            self.redis_client = None
            self._sessions[session_id] = session_data
        
        return session_id
    
    async def revoke_token(self, token: str, ttl_hours: int = 24):
        """Add token to blacklist."""
        token_hash = hash(token)
        ttl_seconds = ttl_hours * 60 * 60
        try:
            if self.redis_client is not None:
                self.redis_client.setex(f"blacklist:{token_hash}", ttl_seconds, "revoked")
            else:
                self._blacklist.add(token)
        except Exception as e:
            logger.warning(f"Redis blacklist write failed, storing in memory: {e}")
            self.redis_client = None
            self._blacklist.add(token)
    
    async def revoke_api_key(self, api_key: str):
        """Revoke API key."""
        try:
            key_data = None
            if self.redis_client is not None:
                key_data = self.redis_client.get(f"api_key:{api_key}")
            if key_data:
                import json
                data = json.loads(key_data)
                data["active"] = False
                if self.redis_client is not None:
                    self.redis_client.set(f"api_key:{api_key}", json.dumps(data))
                else:
                    self._api_keys[api_key] = data
            else:
                # Update memory store if present
                if api_key in self._api_keys:
                    self._api_keys[api_key]["active"] = False
        except Exception as e:
            logger.warning(f"Redis API key revoke failed, updating memory: {e}")
            self.redis_client = None
            if api_key in self._api_keys:
                self._api_keys[api_key]["active"] = False
    
    async def revoke_session(self, session_id: str):
        """Revoke session."""
        try:
            if self.redis_client is not None:
                self.redis_client.delete(f"session:{session_id}")
            if session_id in self._sessions:
                del self._sessions[session_id]
        except Exception as e:
            logger.warning(f"Redis session revoke failed, updating memory: {e}")
            self.redis_client = None
            if session_id in self._sessions:
                del self._sessions[session_id]
    
    def check_permission(self, user_info: Dict[str, Any], required_permission: str) -> bool:
        """Check if user has required permission."""
        permissions = user_info.get("permissions", [])
        roles = user_info.get("roles", [])
        
        # Check direct permission
        if required_permission in permissions:
            return True
            
        # Check role-based permissions (admin has all permissions)
        if "admin" in roles:
            return True
            
        return False
    
    def check_role(self, user_info: Dict[str, Any], required_role: str) -> bool:
        """Check if user has required role."""
        roles = user_info.get("roles", [])
        return required_role in roles

# Global auth middleware instance
auth_middleware = WebSocketAuthMiddleware()
