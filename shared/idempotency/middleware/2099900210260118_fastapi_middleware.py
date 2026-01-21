# doc_id: DOC-SERVICE-0199
# DOC_ID: DOC-SERVICE-0109
"""
FastAPI middleware for idempotency support in EAFIX trading system.
Automatically handles idempotency for HTTP requests with idempotency keys.
"""

import asyncio
import json
from typing import Any, Callable, Dict, Optional, Set
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

from ..models.idempotency_key import (
    IdempotencyRequest, IdempotencyResponse, IdempotencyStatus,
    OperationType
)
from ..stores.redis_store import RedisIdempotencyStore

logger = structlog.get_logger(__name__)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic idempotency handling.
    
    Features:
    - Automatic idempotency key extraction from headers
    - Request/response caching
    - Duplicate request detection
    - Configurable idempotency per endpoint
    """
    
    def __init__(
        self,
        app: ASGIApp,
        idempotency_store: RedisIdempotencyStore,
        idempotent_methods: Set[str] = None,
        idempotency_header: str = "Idempotency-Key",
        service_name: str = "trading-service",
        default_ttl_seconds: int = 3600,
        max_body_size: int = 1024 * 1024,  # 1MB
        excluded_paths: Set[str] = None
    ):
        """
        Initialize idempotency middleware.
        
        Args:
            app: ASGI application
            idempotency_store: Idempotency store implementation
            idempotent_methods: HTTP methods that support idempotency
            idempotency_header: Header name for idempotency key
            service_name: Name of the service
            default_ttl_seconds: Default TTL for idempotency records
            max_body_size: Maximum request body size to cache
            excluded_paths: Paths to exclude from idempotency
        """
        super().__init__(app)
        self.store = idempotency_store
        self.idempotent_methods = idempotent_methods or {"POST", "PUT", "PATCH"}
        self.idempotency_header = idempotency_header
        self.service_name = service_name
        self.default_ttl = default_ttl_seconds
        self.max_body_size = max_body_size
        self.excluded_paths = excluded_paths or {
            "/healthz", "/metrics", "/docs", "/openapi.json"
        }
        
        # Operation type mapping based on path patterns
        self.path_operation_mapping = {
            "/execute": OperationType.ORDER_SUBMIT,
            "/cancel": OperationType.ORDER_CANCEL,
            "/modify": OperationType.ORDER_MODIFY,
            "/signals": OperationType.SIGNAL_GENERATE,
            "/validate": OperationType.RISK_VALIDATE,
            "/ingest": OperationType.PRICE_INGEST,
            "/indicators": OperationType.INDICATOR_COMPUTE,
            "/reports": OperationType.REPORT_GENERATE,
            "/compliance": OperationType.COMPLIANCE_CHECK,
        }
    
    def _should_apply_idempotency(self, request: Request) -> bool:
        """Check if idempotency should be applied to this request."""
        # Check method
        if request.method not in self.idempotent_methods:
            return False
        
        # Check excluded paths
        path = request.url.path
        if any(excluded in path for excluded in self.excluded_paths):
            return False
        
        # Check for idempotency header
        return self.idempotency_header in request.headers
    
    def _get_operation_type(self, request: Request) -> OperationType:
        """Determine operation type from request path."""
        path = request.url.path.lower()
        
        # Check path patterns
        for pattern, operation in self.path_operation_mapping.items():
            if pattern in path:
                return operation
        
        # Default based on method
        if request.method == "POST":
            return OperationType.ORDER_SUBMIT
        elif request.method == "PUT":
            return OperationType.ORDER_MODIFY
        elif request.method == "DELETE":
            return OperationType.ORDER_CANCEL
        else:
            return OperationType.ORDER_SUBMIT  # Default fallback
    
    async def _read_body(self, request: Request) -> Dict[str, Any]:
        """Read and parse request body."""
        try:
            body = await request.body()
            
            # Skip large bodies
            if len(body) > self.max_body_size:
                logger.warning(
                    "Request body too large for idempotency caching",
                    size=len(body),
                    max_size=self.max_body_size
                )
                return {"_body_too_large": True, "size": len(body)}
            
            # Parse JSON body
            if body:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    return json.loads(body.decode("utf-8"))
                else:
                    return {"_raw_body": body.decode("utf-8", errors="ignore")}
            
            return {}
            
        except Exception as e:
            logger.warning("Error reading request body", error=str(e))
            return {"_body_error": str(e)}
    
    async def _create_idempotency_request(
        self,
        request: Request,
        idempotency_key: str
    ) -> IdempotencyRequest:
        """Create idempotency request from HTTP request."""
        # Read request body
        payload = await self._read_body(request)
        
        # Add request metadata
        payload.update({
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": {
                k: v for k, v in request.headers.items()
                if k.lower() not in {"authorization", "cookie", "x-api-key"}
            },
        })
        
        return IdempotencyRequest(
            idempotency_key=idempotency_key,
            operation_type=self._get_operation_type(request),
            service=self.service_name,
            payload=payload,
            client_id=request.headers.get("x-client-id"),
            timeout_seconds=self.default_ttl,
            created_at=datetime.now(timezone.utc)
        )
    
    async def _create_response_from_result(
        self,
        idempotency_response: IdempotencyResponse
    ) -> Response:
        """Create HTTP response from idempotency result."""
        if idempotency_response.status == IdempotencyStatus.COMPLETED:
            if idempotency_response.result:
                # Return cached successful response
                result = idempotency_response.result
                status_code = result.get("status_code", 200)
                headers = result.get("headers", {})
                body = result.get("body", {})
                
                return JSONResponse(
                    content=body,
                    status_code=status_code,
                    headers={
                        **headers,
                        "X-Idempotency-Key": idempotency_response.idempotency_key,
                        "X-Idempotency-Status": "hit",
                        "X-Idempotency-Created": idempotency_response.created_at.isoformat()
                    }
                )
            
        elif idempotency_response.status == IdempotencyStatus.FAILED:
            # Return cached error response
            error_msg = idempotency_response.error or "Operation failed"
            return JSONResponse(
                content={"error": error_msg, "idempotency_key": idempotency_response.idempotency_key},
                status_code=400,
                headers={
                    "X-Idempotency-Key": idempotency_response.idempotency_key,
                    "X-Idempotency-Status": "failed"
                }
            )
            
        elif idempotency_response.status == IdempotencyStatus.IN_PROGRESS:
            # Return 409 Conflict for in-progress operations
            return JSONResponse(
                content={
                    "message": "Operation in progress",
                    "idempotency_key": idempotency_response.idempotency_key,
                    "status": "in_progress",
                    "created_at": idempotency_response.created_at.isoformat()
                },
                status_code=409,
                headers={
                    "X-Idempotency-Key": idempotency_response.idempotency_key,
                    "X-Idempotency-Status": "in_progress",
                    "Retry-After": "5"
                }
            )
        
        # Default case (shouldn't happen)
        return JSONResponse(
            content={
                "message": "Unknown idempotency status",
                "idempotency_key": idempotency_response.idempotency_key,
                "status": idempotency_response.status
            },
            status_code=500
        )
    
    async def _cache_successful_response(
        self,
        idempotency_key: str,
        response: Response
    ) -> bool:
        """Cache successful response for idempotency."""
        try:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Parse response data
            try:
                body_dict = json.loads(body.decode("utf-8"))
            except:
                body_dict = {"_raw_response": body.decode("utf-8", errors="ignore")}
            
            # Create result data
            result_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": body_dict
            }
            
            # Update idempotency record
            await self.store.update_status(
                idempotency_key=idempotency_key,
                status=IdempotencyStatus.COMPLETED,
                result=result_data
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Error caching successful response",
                idempotency_key=idempotency_key,
                error=str(e)
            )
            return False
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with idempotency support."""
        # Check if idempotency should be applied
        if not self._should_apply_idempotency(request):
            return await call_next(request)
        
        idempotency_key = request.headers[self.idempotency_header]
        
        try:
            # Create idempotency request
            idempotency_request = await self._create_idempotency_request(
                request, idempotency_key
            )
            
            # Check for existing operation
            existing_response, is_new = await self.store.check_and_create(
                idempotency_request, self.default_ttl
            )
            
            if not is_new:
                # Return cached response
                logger.info(
                    "Returning cached idempotency response",
                    idempotency_key=idempotency_key,
                    status=existing_response.status
                )
                return await self._create_response_from_result(existing_response)
            
            # Mark operation as in progress
            await self.store.update_status(
                idempotency_key=idempotency_key,
                status=IdempotencyStatus.IN_PROGRESS
            )
            
            # Process the request
            try:
                response = await call_next(request)
                
                # Cache successful response
                if 200 <= response.status_code < 300:
                    await self._cache_successful_response(idempotency_key, response)
                    
                    # Add idempotency headers
                    response.headers["X-Idempotency-Key"] = idempotency_key
                    response.headers["X-Idempotency-Status"] = "miss"
                    
                else:
                    # Cache error response
                    await self.store.update_status(
                        idempotency_key=idempotency_key,
                        status=IdempotencyStatus.FAILED,
                        error=f"HTTP {response.status_code}"
                    )
                    
                    response.headers["X-Idempotency-Key"] = idempotency_key
                    response.headers["X-Idempotency-Status"] = "failed"
                
                return response
                
            except Exception as e:
                # Mark operation as failed
                await self.store.update_status(
                    idempotency_key=idempotency_key,
                    status=IdempotencyStatus.FAILED,
                    error=str(e)
                )
                
                logger.error(
                    "Operation failed during processing",
                    idempotency_key=idempotency_key,
                    error=str(e)
                )
                
                # Re-raise the exception
                raise
                
        except Exception as e:
            logger.error(
                "Error in idempotency middleware",
                idempotency_key=idempotency_key,
                error=str(e)
            )
            
            # Return error response
            return JSONResponse(
                content={
                    "error": "Idempotency processing failed",
                    "details": str(e)
                },
                status_code=500
            )


def add_idempotency_middleware(
    app: FastAPI,
    idempotency_store: RedisIdempotencyStore,
    **kwargs
) -> None:
    """
    Add idempotency middleware to FastAPI application.
    
    Args:
        app: FastAPI application
        idempotency_store: Idempotency store instance
        **kwargs: Additional middleware configuration
    """
    middleware = IdempotencyMiddleware(
        app=app,
        idempotency_store=idempotency_store,
        **kwargs
    )
    
    app.add_middleware(BaseHTTPMiddleware, dispatch=middleware.dispatch)
    
    logger.info(
        "Added idempotency middleware to FastAPI application",
        service_name=kwargs.get("service_name", "trading-service")
    )


# Decorator for marking specific endpoints as idempotent
def idempotent(
    operation_type: Optional[OperationType] = None,
    ttl_seconds: Optional[int] = None,
    required: bool = True
):
    """
    Decorator to mark endpoint as requiring idempotency.
    
    Args:
        operation_type: Specific operation type for this endpoint
        ttl_seconds: TTL for idempotency records
        required: Whether idempotency key is required
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        # Store metadata on function
        func._idempotent = True
        func._idempotency_operation_type = operation_type
        func._idempotency_ttl = ttl_seconds
        func._idempotency_required = required
        
        return func
    
    return decorator


# Example usage functions for common trading operations
async def create_idempotent_order_handler(
    app: FastAPI,
    idempotency_store: RedisIdempotencyStore
):
    """Example of creating an idempotent order submission handler."""
    
    @app.post("/orders")
    @idempotent(operation_type=OperationType.ORDER_SUBMIT, ttl_seconds=1800)
    async def submit_order(
        request: Request,
        order_data: dict
    ):
        """Submit trading order with idempotency support."""
        # The middleware handles idempotency automatically
        # This handler just implements the business logic
        
        # Simulate order processing
        await asyncio.sleep(0.1)
        
        return {
            "order_id": f"order_{hash(str(order_data))[:8]}",
            "status": "submitted",
            "symbol": order_data.get("symbol"),
            "quantity": order_data.get("quantity"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    logger.info("Created idempotent order handler")


async def create_idempotent_signal_handler(
    app: FastAPI,
    idempotency_store: RedisIdempotencyStore
):
    """Example of creating an idempotent signal generation handler."""
    
    @app.post("/signals")
    @idempotent(operation_type=OperationType.SIGNAL_GENERATE, ttl_seconds=600)
    async def generate_signal(
        request: Request,
        signal_params: dict
    ):
        """Generate trading signal with idempotency support."""
        
        # Simulate signal generation
        await asyncio.sleep(0.05)
        
        return {
            "signal_id": f"signal_{hash(str(signal_params))[:8]}",
            "symbol": signal_params.get("symbol"),
            "direction": signal_params.get("direction", "long"),
            "confidence": 0.75,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    logger.info("Created idempotent signal handler")