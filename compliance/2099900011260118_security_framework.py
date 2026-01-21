# doc_id: DOC-DOC-0023
# DOC_ID: DOC-SERVICE-0003
# packages/security/src/security/framework.py

import asyncio
import hashlib
import secrets
import time
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import json
import logging

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis.asyncio as redis

from .audit import AuditLogger
from .sandbox import SandboxManager
from .rbac import RoleBasedAccessControl


class Permission(Enum):
    """System permissions"""
    # Process permissions
    PROCESS_READ = "process:read"
    PROCESS_WRITE = "process:write"
    PROCESS_DELETE = "process:delete"
    PROCESS_EXECUTE = "process:execute"
    
    # Trading permissions
    TRADING_VIEW = "trading:view"
    TRADING_PLACE_ORDER = "trading:place_order"
    TRADING_CANCEL_ORDER = "trading:cancel_order"
    TRADING_MODIFY_ORDER = "trading:modify_order"
    
    # Admin permissions
    ADMIN_USER_MANAGEMENT = "admin:user_management"
    ADMIN_SYSTEM_CONFIG = "admin:system_config"
    ADMIN_AUDIT_VIEW = "admin:audit_view"
    
    # Data permissions
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_EXPORT = "data:export"


class Role(Enum):
    """System roles"""
    GUEST = "guest"
    TRADER = "trader"
    DEVELOPER = "developer"
    ADMIN = "admin"
    SYSTEM = "system"


@dataclass
class User:
    """User entity"""
    id: str
    username: str
    email: str
    roles: Set[Role] = field(default_factory=set)
    permissions: Set[Permission] = field(default_factory=set)
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    last_login: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    jwt_secret: str
    jwt_expiry_hours: int = 24
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    password_min_length: int = 8
    require_mfa: bool = False
    session_timeout_minutes: int = 480
    allowed_origins: List[str] = field(default_factory=list)
    rate_limit_per_minute: int = 100


class SecurityFramework:
    """
    Comprehensive security framework providing:
    - JWT-based authentication
    - Role-based access control
    - Audit logging
    - Sandbox execution
    - Rate limiting
    """
    
    def __init__(self, policy: SecurityPolicy, redis_client: redis.Redis):
        self.policy = policy
        self.redis = redis_client
        
        # Core components
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.rbac = RoleBasedAccessControl()
        self.audit = AuditLogger(redis_client)
        self.sandbox = SandboxManager()
        
        # Security state
        self._users: Dict[str, User] = {}
        self._sessions: Dict[str, Dict] = {}
        self._rate_limits: Dict[str, List[float]] = {}
        
        self._setup_default_permissions()
    
    def _setup_default_permissions(self):
        """Setup default role permissions"""
        
        # Guest permissions
        self.rbac.assign_permissions_to_role(Role.GUEST, [
            Permission.PROCESS_READ,
            Permission.DATA_READ
        ])
        
        # Trader permissions
        self.rbac.assign_permissions_to_role(Role.TRADER, [
            Permission.PROCESS_READ,
            Permission.PROCESS_EXECUTE,
            Permission.TRADING_VIEW,
            Permission.TRADING_PLACE_ORDER,
            Permission.TRADING_CANCEL_ORDER,
            Permission.TRADING_MODIFY_ORDER,
            Permission.DATA_READ
        ])
        
        # Developer permissions
        self.rbac.assign_permissions_to_role(Role.DEVELOPER, [
            Permission.PROCESS_READ,
            Permission.PROCESS_WRITE,
            Permission.PROCESS_EXECUTE,
            Permission.DATA_READ,
            Permission.DATA_WRITE
        ])
        
        # Admin permissions (all)
        self.rbac.assign_permissions_to_role(Role.ADMIN, list(Permission))
    
    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        roles: Set[Role] = None
    ) -> User:
        """Create new user"""
        
        if username in self._users:
            raise ValueError(f"User {username} already exists")
        
        # Validate password
        if len(password) < self.policy.password_min_length:
            raise ValueError(f"Password must be at least {self.policy.password_min_length} characters")
        
        user = User(
            id=secrets.token_urlsafe(16),
            username=username,
            email=email,
            roles=roles or {Role.GUEST}
        )
        
        # Hash password
        password_hash = self.pwd_context.hash(password)
        await self.redis.set(f"user:password:{user.id}", password_hash, ex=86400*30)
        
        # Calculate permissions from roles
        user.permissions = self.rbac.get_permissions_for_roles(user.roles)
        
        self._users[username] = user
        
        await self.audit.log_event(
            user_id=user.id,
            action="user_created",
            resource="user",
            resource_id=user.id,
            details={"username": username, "email": email, "roles": [r.value for r in roles]}
        )
        
        return user
    
    async def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token"""
        
        user = self._users.get(username)
        if not user or not user.is_active:
            await self.audit.log_event(
                user_id=username,
                action="login_failed",
                resource="auth",
                details={"reason": "user_not_found"}
            )
            return None
        
        # Check lockout
        lockout_key = f"lockout:{user.id}"
        if await self.redis.get(lockout_key):
            await self.audit.log_event(
                user_id=user.id,
                action="login_failed",
                resource="auth",
                details={"reason": "account_locked"}
            )
            return None
        
        # Verify password
        password_hash = await self.redis.get(f"user:password:{user.id}")
        if not password_hash or not self.pwd_context.verify(password, password_hash.decode()):
            
            # Track failed attempts
            attempts_key = f"attempts:{user.id}"
            attempts = await self.redis.incr(attempts_key)
            await self.redis.expire(attempts_key, 300)  # 5 minutes
            
            if attempts >= self.policy.max_login_attempts:
                await self.redis.set(
                    lockout_key,
                    "locked",
                    ex=self.policy.lockout_duration_minutes * 60
                )
                await self.audit.log_event(
                    user_id=user.id,
                    action="account_locked",
                    resource="auth",
                    details={"attempts": attempts}
                )
            
            await self.audit.log_event(
                user_id=user.id,
                action="login_failed",
                resource="auth",
                details={"reason": "invalid_password", "attempts": attempts}
            )
            return None
        
        # Clear failed attempts
        await self.redis.delete(f"attempts:{user.id}")
        
        # Update last login
        user.last_login = time.time()
        
        # Generate JWT
        token = self._generate_jwt(user)
        
        # Store session
        session_id = secrets.token_urlsafe(32)
        session_data = {
            "user_id": user.id,
            "username": user.username,
            "roles": [r.value for r in user.roles],
            "permissions": [p.value for p in user.permissions],
            "created_at": time.time()
        }
        
        await self.redis.set(
            f"session:{session_id}",
            json.dumps(session_data),
            ex=self.policy.session_timeout_minutes * 60
        )
        
        await self.audit.log_event(
            user_id=user.id,
            action="login_success",
            resource="auth",
            details={"session_id": session_id}
        )
        
        return token
    
    def _generate_jwt(self, user: User) -> str:
        """Generate JWT token for user"""
        
        payload = {
            "user_id": user.id,
            "username": user.username,
            "roles": [r.value for r in user.roles],
            "permissions": [p.value for p in user.permissions],
            "exp": time.time() + (self.policy.jwt_expiry_hours * 3600),
            "iat": time.time(),
            "iss": "eafix-security"
        }
        
        return jwt.encode(payload, self.policy.jwt_secret, algorithm="HS256")
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        
        try:
            payload = jwt.decode(
                token,
                self.policy.jwt_secret,
                algorithms=["HS256"],
                options={"verify_exp": True}
            )
            
            # Verify user still exists and is active
            user = self._users.get(payload["username"])
            if not user or not user.is_active:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            await self.audit.log_event(
                user_id="unknown",
                action="token_expired",
                resource="auth"
            )
            return None
        except jwt.InvalidTokenError:
            await self.audit.log_event(
                user_id="unknown",
                action="token_invalid",
                resource="auth"
            )
            return None
    
    async def logout(self, token: str) -> bool:
        """Logout user and invalidate session"""
        
        payload = await self.verify_token(token)
        if not payload:
            return False
        
        # Add token to blacklist
        await self.redis.set(
            f"blacklist:{token}",
            "revoked",
            ex=self.policy.jwt_expiry_hours * 3600
        )
        
        await self.audit.log_event(
            user_id=payload["user_id"],
            action="logout",
            resource="auth"
        )
        
        return True
    
    async def check_permission(
        self,
        user_id: str,
        permission: Permission,
        resource_id: str = None
    ) -> bool:
        """Check if user has specific permission"""
        
        user = next((u for u in self._users.values() if u.id == user_id), None)
        if not user or not user.is_active:
            return False
        
        has_permission = permission in user.permissions
        
        await self.audit.log_event(
            user_id=user_id,
            action="permission_check",
            resource="rbac",
            resource_id=resource_id,
            details={
                "permission": permission.value,
                "granted": has_permission
            }
        )
        
        return has_permission
    
    async def rate_limit_check(self, user_id: str, endpoint: str) -> bool:
        """Check rate limiting for user/endpoint"""
        
        key = f"rate_limit:{user_id}:{endpoint}"
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        
        # Get current requests in window
        requests = await self.redis.zrangebyscore(key, window_start, current_time)
        
        if len(requests) >= self.policy.rate_limit_per_minute:
            await self.audit.log_event(
                user_id=user_id,
                action="rate_limit_exceeded",
                resource="rate_limit",
                details={"endpoint": endpoint, "requests": len(requests)}
            )
            return False
        
        # Add current request
        await self.redis.zadd(key, {str(current_time): current_time})
        await self.redis.expire(key, 60)
        
        return True
    
    @asynccontextmanager
    async def secure_execution(
        self,
        user_id: str,
        code: str,
        permissions: List[Permission] = None
    ):
        """Execute code in secure sandbox"""
        
        # Check permissions
        required_perms = permissions or [Permission.PROCESS_EXECUTE]
        for perm in required_perms:
            if not await self.check_permission(user_id, perm):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission {perm.value} required"
                )
        
        await self.audit.log_event(
            user_id=user_id,
            action="sandbox_execution_start",
            resource="sandbox",
            details={"code_hash": hashlib.sha256(code.encode()).hexdigest()}
        )
        
        try:
            async with self.sandbox.execute(code) as result:
                yield result
                
            await self.audit.log_event(
                user_id=user_id,
                action="sandbox_execution_success",
                resource="sandbox"
            )
            
        except Exception as e:
            await self.audit.log_event(
                user_id=user_id,
                action="sandbox_execution_failed",
                resource="sandbox",
                details={"error": str(e)}
            )
            raise


# FastAPI Integration Classes

class JWTBearer(HTTPBearer):
    """JWT Bearer token authentication"""
    
    def __init__(self, security: SecurityFramework):
        super().__init__(auto_error=True)
        self.security = security
    
    async def __call__(self, request: Request) -> Dict[str, Any]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if credentials.scheme != "Bearer":
            raise HTTPException(
                status_code=403,
                detail="Invalid authentication scheme"
            )
        
        # Check if token is blacklisted
        is_blacklisted = await self.security.redis.get(f"blacklist:{credentials.credentials}")
        if is_blacklisted:
            raise HTTPException(
                status_code=403,
                detail="Token has been revoked"
            )
        
        payload = await self.security.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=403,
                detail="Invalid or expired token"
            )
        
        return payload


def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Extract user from request context
            request = kwargs.get('request')
            if not request:
                raise HTTPException(status_code=500, detail="Request context required")
            
            user_data = getattr(request.state, 'user', None)
            if not user_data:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Check permission
            if permission.value not in user_data.get('permissions', []):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission {permission.value} required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(role: Role):
    """Decorator to require specific role"""
    
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if not request:
                raise HTTPException(status_code=500, detail="Request context required")
            
            user_data = getattr(request.state, 'user', None)
            if not user_data:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if role.value not in user_data.get('roles', []):
                raise HTTPException(
                    status_code=403,
                    detail=f"Role {role.value} required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator