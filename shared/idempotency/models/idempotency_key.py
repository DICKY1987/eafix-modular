"""
Idempotency key models for EAFIX trading system.
Provides deterministic, collision-resistant keys for trading operations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import uuid
from pydantic import BaseModel, Field, validator


class OperationType(str, Enum):
    """Trading operation types that support idempotency."""
    ORDER_SUBMIT = "order_submit"
    ORDER_CANCEL = "order_cancel"
    ORDER_MODIFY = "order_modify"
    POSITION_CLOSE = "position_close"
    SIGNAL_GENERATE = "signal_generate"
    RISK_VALIDATE = "risk_validate"
    PRICE_INGEST = "price_ingest"
    INDICATOR_COMPUTE = "indicator_compute"
    REPORT_GENERATE = "report_generate"
    COMPLIANCE_CHECK = "compliance_check"


class IdempotencyStatus(str, Enum):
    """Status of idempotent operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass(frozen=True)
class IdempotencyKey:
    """
    Deterministic idempotency key for trading operations.
    
    Format: {operation_type}:{service}:{deterministic_hash}
    Example: order_submit:execution-engine:a1b2c3d4e5f6
    """
    operation_type: OperationType
    service: str
    deterministic_hash: str
    
    def __str__(self) -> str:
        return f"{self.operation_type.value}:{self.service}:{self.deterministic_hash}"
    
    def __post_init__(self):
        """Validate key components."""
        if not self.service:
            raise ValueError("Service name cannot be empty")
        if len(self.deterministic_hash) < 8:
            raise ValueError("Hash must be at least 8 characters")
        if not all(c.isalnum() or c in "-_" for c in self.service):
            raise ValueError("Service name must be alphanumeric with hyphens/underscores")


class IdempotencyRequest(BaseModel):
    """Request model for idempotent operations."""
    
    idempotency_key: str = Field(..., description="Client-provided idempotency key")
    operation_type: OperationType = Field(..., description="Type of operation")
    service: str = Field(..., description="Service name")
    payload: Dict[str, Any] = Field(..., description="Operation payload")
    client_id: Optional[str] = Field(None, description="Client identifier")
    timeout_seconds: int = Field(300, description="Operation timeout in seconds")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('idempotency_key')
    def validate_idempotency_key(cls, v):
        """Validate idempotency key format."""
        if not v or len(v) < 10:
            raise ValueError("Idempotency key must be at least 10 characters")
        return v
    
    @validator('timeout_seconds')
    def validate_timeout(cls, v):
        """Validate timeout is reasonable."""
        if v < 1 or v > 3600:  # 1 second to 1 hour
            raise ValueError("Timeout must be between 1 and 3600 seconds")
        return v
    
    def get_deterministic_hash(self) -> str:
        """Generate deterministic hash from payload."""
        return generate_deterministic_hash(self.payload)


class IdempotencyResponse(BaseModel):
    """Response model for idempotent operations."""
    
    idempotency_key: str = Field(..., description="Original idempotency key")
    status: IdempotencyStatus = Field(..., description="Operation status")
    result: Optional[Dict[str, Any]] = Field(None, description="Operation result")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="When operation was created")
    updated_at: datetime = Field(..., description="When operation was last updated")
    completed_at: Optional[datetime] = Field(None, description="When operation completed")
    expires_at: datetime = Field(..., description="When result expires")
    retry_count: int = Field(0, description="Number of retries")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


def generate_deterministic_hash(payload: Dict[str, Any], length: int = 12) -> str:
    """
    Generate deterministic hash from payload.
    
    Args:
        payload: Dictionary to hash
        length: Length of resulting hash (default 12)
        
    Returns:
        Deterministic hash string
    """
    # Normalize payload for consistent hashing
    normalized = normalize_for_hashing(payload)
    
    # Generate SHA-256 hash
    hasher = hashlib.sha256()
    hasher.update(normalized.encode('utf-8'))
    
    # Return truncated hex digest
    return hasher.hexdigest()[:length]


def normalize_for_hashing(payload: Any) -> str:
    """
    Normalize payload for consistent hashing.
    
    Args:
        payload: Data to normalize
        
    Returns:
        Normalized JSON string
    """
    if isinstance(payload, dict):
        # Sort keys and normalize values recursively
        normalized = {k: normalize_for_hashing(v) for k, v in sorted(payload.items())}
        return json.dumps(normalized, separators=(',', ':'), sort_keys=True)
    elif isinstance(payload, list):
        # Normalize each item in list
        return json.dumps([normalize_for_hashing(item) for item in payload], 
                         separators=(',', ':'))
    elif isinstance(payload, (str, int, float, bool)) or payload is None:
        return json.dumps(payload, separators=(',', ':'))
    else:
        # Convert to string for other types
        return json.dumps(str(payload), separators=(',', ':'))


def create_idempotency_key(
    operation_type: OperationType,
    service: str,
    payload: Dict[str, Any],
    additional_context: Optional[Dict[str, Any]] = None
) -> IdempotencyKey:
    """
    Create idempotency key for trading operation.
    
    Args:
        operation_type: Type of operation
        service: Service performing operation
        payload: Operation payload
        additional_context: Additional context for key generation
        
    Returns:
        Idempotency key instance
    """
    # Combine payload with additional context
    key_data = payload.copy() if payload else {}
    if additional_context:
        key_data.update(additional_context)
    
    # Generate deterministic hash
    hash_value = generate_deterministic_hash(key_data)
    
    return IdempotencyKey(
        operation_type=operation_type,
        service=service,
        deterministic_hash=hash_value
    )


def create_trading_order_key(
    symbol: str,
    side: str,  # "buy" or "sell"
    quantity: float,
    price: Optional[float] = None,
    order_type: str = "market",
    client_order_id: Optional[str] = None,
    timestamp: Optional[datetime] = None
) -> IdempotencyKey:
    """
    Create idempotency key for trading orders.
    
    Args:
        symbol: Trading symbol (e.g., "EURUSD")
        side: Order side ("buy" or "sell")
        quantity: Order quantity
        price: Order price (for limit orders)
        order_type: Order type ("market", "limit", "stop")
        client_order_id: Client-provided order ID
        timestamp: Order timestamp
        
    Returns:
        Idempotency key for order
    """
    payload = {
        "symbol": symbol.upper(),
        "side": side.lower(),
        "quantity": round(float(quantity), 6),  # Normalize precision
        "order_type": order_type.lower(),
    }
    
    if price is not None:
        payload["price"] = round(float(price), 5)  # Normalize price precision
    
    if client_order_id:
        payload["client_order_id"] = client_order_id
    
    # Use timestamp for time-sensitive uniqueness
    if timestamp:
        payload["timestamp"] = timestamp.isoformat()
    
    return create_idempotency_key(
        operation_type=OperationType.ORDER_SUBMIT,
        service="execution-engine",
        payload=payload
    )


def create_signal_key(
    symbol: str,
    signal_type: str,
    direction: str,  # "long", "short", "close"
    confidence: float,
    indicator_values: Dict[str, float],
    timestamp: datetime
) -> IdempotencyKey:
    """
    Create idempotency key for trading signals.
    
    Args:
        symbol: Trading symbol
        signal_type: Type of signal (e.g., "friday_vol", "momentum")
        direction: Signal direction
        confidence: Signal confidence score
        indicator_values: Indicator values used
        timestamp: Signal timestamp
        
    Returns:
        Idempotency key for signal
    """
    payload = {
        "symbol": symbol.upper(),
        "signal_type": signal_type,
        "direction": direction.lower(),
        "confidence": round(float(confidence), 4),
        "indicators": {k: round(float(v), 6) for k, v in indicator_values.items()},
        "timestamp": timestamp.isoformat()
    }
    
    return create_idempotency_key(
        operation_type=OperationType.SIGNAL_GENERATE,
        service="signal-generator",
        payload=payload
    )


def create_risk_validation_key(
    signal_id: str,
    account_balance: float,
    position_size: float,
    risk_params: Dict[str, Any],
    timestamp: datetime
) -> IdempotencyKey:
    """
    Create idempotency key for risk validation.
    
    Args:
        signal_id: ID of signal being validated
        account_balance: Current account balance
        position_size: Requested position size
        risk_params: Risk validation parameters
        timestamp: Validation timestamp
        
    Returns:
        Idempotency key for risk validation
    """
    payload = {
        "signal_id": signal_id,
        "account_balance": round(float(account_balance), 2),
        "position_size": round(float(position_size), 6),
        "risk_params": normalize_for_hashing(risk_params),
        "timestamp": timestamp.isoformat()
    }
    
    return create_idempotency_key(
        operation_type=OperationType.RISK_VALIDATE,
        service="risk-manager",
        payload=payload
    )


def is_expired(response: IdempotencyResponse) -> bool:
    """Check if idempotency response has expired."""
    return datetime.now(timezone.utc) > response.expires_at


def should_retry(response: IdempotencyResponse, max_retries: int = 3) -> bool:
    """Check if operation should be retried."""
    return (
        response.status == IdempotencyStatus.FAILED and
        response.retry_count < max_retries and
        not is_expired(response)
    )