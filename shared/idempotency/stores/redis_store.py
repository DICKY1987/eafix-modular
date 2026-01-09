# DOC_ID: DOC-SERVICE-0114
"""
Redis-based idempotency store for EAFIX trading system.
Provides distributed idempotency storage with expiration and atomic operations.
"""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import redis.asyncio as redis
from redis.asyncio import Redis
import structlog

from ..models.idempotency_key import (
    IdempotencyRequest, IdempotencyResponse, IdempotencyStatus,
    OperationType, is_expired
)

logger = structlog.get_logger(__name__)


class RedisIdempotencyStore:
    """
    Redis-based idempotency store with atomic operations.
    
    Features:
    - Atomic check-and-set operations
    - Automatic expiration
    - Distributed locking
    - Operation status tracking
    - Result caching
    """
    
    def __init__(
        self,
        redis_client: Redis,
        default_ttl_seconds: int = 3600,  # 1 hour
        lock_timeout_seconds: int = 30,
        key_prefix: str = "idempotency"
    ):
        """
        Initialize Redis idempotency store.
        
        Args:
            redis_client: Redis client instance
            default_ttl_seconds: Default TTL for idempotency records
            lock_timeout_seconds: Timeout for distributed locks
            key_prefix: Prefix for Redis keys
        """
        self.redis = redis_client
        self.default_ttl = default_ttl_seconds
        self.lock_timeout = lock_timeout_seconds
        self.key_prefix = key_prefix
        
        # Lua scripts for atomic operations
        self._check_and_create_script = None
        self._update_status_script = None
        self._cleanup_expired_script = None
        
    async def initialize(self):
        """Initialize Redis scripts."""
        # Script to atomically check and create idempotency record
        self._check_and_create_script = await self.redis.script_load("""
            local key = KEYS[1]
            local lock_key = KEYS[2]
            local data = ARGV[1]
            local ttl = tonumber(ARGV[2])
            local lock_timeout = tonumber(ARGV[3])
            
            -- Check if record exists
            local existing = redis.call('GET', key)
            if existing then
                return {1, existing}  -- Record exists
            end
            
            -- Try to acquire lock
            local lock_acquired = redis.call('SET', lock_key, '1', 'PX', lock_timeout * 1000, 'NX')
            if not lock_acquired then
                return {0, nil}  -- Could not acquire lock
            end
            
            -- Create record with TTL
            redis.call('SETEX', key, ttl, data)
            return {2, data}  -- Record created
        """)
        
        # Script to atomically update operation status
        self._update_status_script = await self.redis.script_load("""
            local key = KEYS[1]
            local lock_key = KEYS[2]
            local new_data = ARGV[1]
            local ttl = tonumber(ARGV[2])
            
            -- Check if record exists
            local existing = redis.call('GET', key)
            if not existing then
                return 0  -- Record not found
            end
            
            -- Update record
            redis.call('SETEX', key, ttl, new_data)
            
            -- Release lock if it exists
            redis.call('DEL', lock_key)
            
            return 1  -- Updated successfully
        """)
        
        # Script to cleanup expired records
        self._cleanup_expired_script = await self.redis.script_load("""
            local pattern = ARGV[1]
            local batch_size = tonumber(ARGV[2])
            local cursor = ARGV[3]
            
            local scan_result = redis.call('SCAN', cursor, 'MATCH', pattern, 'COUNT', batch_size)
            local new_cursor = scan_result[1]
            local keys = scan_result[2]
            
            local deleted = 0
            for i, key in ipairs(keys) do
                local ttl = redis.call('TTL', key)
                if ttl == -1 then  -- No expiration set
                    redis.call('DEL', key)
                    deleted = deleted + 1
                end
            end
            
            return {new_cursor, deleted}
        """)
        
        logger.info("Redis idempotency store initialized")
    
    def _get_key(self, idempotency_key: str) -> str:
        """Get Redis key for idempotency record."""
        return f"{self.key_prefix}:{idempotency_key}"
    
    def _get_lock_key(self, idempotency_key: str) -> str:
        """Get Redis lock key for idempotency record."""
        return f"{self.key_prefix}:lock:{idempotency_key}"
    
    async def check_and_create(
        self,
        request: IdempotencyRequest,
        ttl_seconds: Optional[int] = None
    ) -> Tuple[IdempotencyResponse, bool]:
        """
        Atomically check for existing operation and create if not found.
        
        Args:
            request: Idempotency request
            ttl_seconds: TTL for the record
            
        Returns:
            Tuple of (response, is_new_operation)
            - is_new_operation: True if this is a new operation, False if existing
        """
        ttl = ttl_seconds or self.default_ttl
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        
        # Create initial response
        response = IdempotencyResponse(
            idempotency_key=request.idempotency_key,
            status=IdempotencyStatus.PENDING,
            created_at=request.created_at,
            updated_at=request.created_at,
            expires_at=expires_at
        )
        
        key = self._get_key(request.idempotency_key)
        lock_key = self._get_lock_key(request.idempotency_key)
        data = response.json()
        
        try:
            # Execute atomic check-and-create
            result = await self._check_and_create_script(
                keys=[key, lock_key],
                args=[data, ttl, self.lock_timeout]
            )
            
            result_code, result_data = result
            
            if result_code == 1:  # Existing record found
                existing_response = IdempotencyResponse.parse_raw(result_data)
                
                # Check if expired
                if is_expired(existing_response):
                    logger.warning(
                        "Found expired idempotency record",
                        idempotency_key=request.idempotency_key,
                        expires_at=existing_response.expires_at
                    )
                    # Delete expired record and retry
                    await self.redis.delete(key)
                    return await self.check_and_create(request, ttl_seconds)
                
                logger.info(
                    "Found existing idempotency record",
                    idempotency_key=request.idempotency_key,
                    status=existing_response.status
                )
                return existing_response, False
                
            elif result_code == 2:  # New record created
                logger.info(
                    "Created new idempotency record",
                    idempotency_key=request.idempotency_key,
                    ttl=ttl
                )
                return response, True
                
            else:  # Could not acquire lock
                logger.warning(
                    "Could not acquire lock for idempotency operation",
                    idempotency_key=request.idempotency_key
                )
                # Wait briefly and retry
                await asyncio.sleep(0.1)
                return await self.check_and_create(request, ttl_seconds)
                
        except Exception as e:
            logger.error(
                "Error in check_and_create",
                idempotency_key=request.idempotency_key,
                error=str(e)
            )
            raise
    
    async def update_status(
        self,
        idempotency_key: str,
        status: IdempotencyStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Update operation status atomically.
        
        Args:
            idempotency_key: Idempotency key
            status: New status
            result: Operation result (if completed)
            error: Error message (if failed)
            ttl_seconds: New TTL for record
            
        Returns:
            True if updated successfully, False if record not found
        """
        key = self._get_key(idempotency_key)
        lock_key = self._get_lock_key(idempotency_key)
        
        try:
            # Get existing record
            existing_data = await self.redis.get(key)
            if not existing_data:
                logger.warning(
                    "Idempotency record not found for update",
                    idempotency_key=idempotency_key
                )
                return False
            
            # Parse and update
            existing_response = IdempotencyResponse.parse_raw(existing_data)
            updated_at = datetime.now(timezone.utc)
            
            # Create updated response
            updated_response = existing_response.copy(update={
                "status": status,
                "updated_at": updated_at,
                "result": result,
                "error": error,
            })
            
            # Set completion time if completed or failed
            if status in (IdempotencyStatus.COMPLETED, IdempotencyStatus.FAILED):
                updated_response.completed_at = updated_at
            
            # Increment retry count if failed
            if status == IdempotencyStatus.FAILED:
                updated_response.retry_count += 1
            
            ttl = ttl_seconds or self.default_ttl
            
            # Execute atomic update
            result = await self._update_status_script(
                keys=[key, lock_key],
                args=[updated_response.json(), ttl]
            )
            
            if result == 1:
                logger.info(
                    "Updated idempotency record status",
                    idempotency_key=idempotency_key,
                    status=status
                )
                return True
            else:
                logger.warning(
                    "Failed to update idempotency record",
                    idempotency_key=idempotency_key
                )
                return False
                
        except Exception as e:
            logger.error(
                "Error updating idempotency status",
                idempotency_key=idempotency_key,
                error=str(e)
            )
            raise
    
    async def get(self, idempotency_key: str) -> Optional[IdempotencyResponse]:
        """
        Get idempotency record.
        
        Args:
            idempotency_key: Idempotency key
            
        Returns:
            Idempotency response or None if not found
        """
        key = self._get_key(idempotency_key)
        
        try:
            data = await self.redis.get(key)
            if not data:
                return None
            
            response = IdempotencyResponse.parse_raw(data)
            
            # Check if expired
            if is_expired(response):
                logger.info(
                    "Removing expired idempotency record",
                    idempotency_key=idempotency_key
                )
                await self.redis.delete(key)
                return None
            
            return response
            
        except Exception as e:
            logger.error(
                "Error getting idempotency record",
                idempotency_key=idempotency_key,
                error=str(e)
            )
            raise
    
    async def delete(self, idempotency_key: str) -> bool:
        """
        Delete idempotency record.
        
        Args:
            idempotency_key: Idempotency key
            
        Returns:
            True if deleted, False if not found
        """
        key = self._get_key(idempotency_key)
        lock_key = self._get_lock_key(idempotency_key)
        
        try:
            # Delete both record and lock
            deleted_count = await self.redis.delete(key, lock_key)
            return deleted_count > 0
            
        except Exception as e:
            logger.error(
                "Error deleting idempotency record",
                idempotency_key=idempotency_key,
                error=str(e)
            )
            raise
    
    async def list_by_operation(
        self,
        operation_type: OperationType,
        status: Optional[IdempotencyStatus] = None,
        limit: int = 100
    ) -> List[IdempotencyResponse]:
        """
        List idempotency records by operation type.
        
        Args:
            operation_type: Operation type to filter by
            status: Optional status filter
            limit: Maximum number of records to return
            
        Returns:
            List of idempotency responses
        """
        pattern = f"{self.key_prefix}:{operation_type.value}:*"
        
        try:
            responses = []
            cursor = 0
            
            while len(responses) < limit:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=min(limit - len(responses), 100)
                )
                
                if not keys:
                    break
                
                # Get all records
                values = await self.redis.mget(*keys)
                
                for value in values:
                    if value:
                        try:
                            response = IdempotencyResponse.parse_raw(value)
                            
                            # Filter by status if specified
                            if status is None or response.status == status:
                                # Skip expired records
                                if not is_expired(response):
                                    responses.append(response)
                                    
                        except Exception as e:
                            logger.warning(
                                "Error parsing idempotency record",
                                error=str(e)
                            )
                
                if cursor == 0:  # Scan complete
                    break
            
            return responses[:limit]
            
        except Exception as e:
            logger.error(
                "Error listing idempotency records",
                operation_type=operation_type,
                error=str(e)
            )
            raise
    
    async def cleanup_expired(self, batch_size: int = 1000) -> int:
        """
        Clean up expired idempotency records.
        
        Args:
            batch_size: Number of keys to process per batch
            
        Returns:
            Number of records cleaned up
        """
        pattern = f"{self.key_prefix}:*"
        total_deleted = 0
        cursor = 0
        
        try:
            while True:
                result = await self._cleanup_expired_script(
                    keys=[],
                    args=[pattern, batch_size, cursor]
                )
                
                cursor, deleted = result
                total_deleted += deleted
                
                if cursor == 0:  # Scan complete
                    break
                
                # Small delay to avoid overwhelming Redis
                if total_deleted > 0:
                    await asyncio.sleep(0.01)
            
            if total_deleted > 0:
                logger.info(
                    "Cleaned up expired idempotency records",
                    deleted_count=total_deleted
                )
            
            return total_deleted
            
        except Exception as e:
            logger.error(
                "Error cleaning up expired records",
                error=str(e)
            )
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get idempotency store statistics.
        
        Returns:
            Dictionary of statistics
        """
        try:
            pattern = f"{self.key_prefix}:*"
            
            # Count total records
            cursor = 0
            total_records = 0
            status_counts = {}
            operation_counts = {}
            
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=1000
                )
                
                if keys:
                    # Filter out lock keys
                    record_keys = [k for k in keys if not k.decode().endswith(':lock')]
                    total_records += len(record_keys)
                    
                    # Get record details for statistics
                    if record_keys:
                        values = await self.redis.mget(*record_keys)
                        
                        for value in values:
                            if value:
                                try:
                                    response = IdempotencyResponse.parse_raw(value)
                                    
                                    # Count by status
                                    status = response.status.value
                                    status_counts[status] = status_counts.get(status, 0) + 1
                                    
                                    # Extract operation type from key
                                    key_parts = response.idempotency_key.split(':', 2)
                                    if len(key_parts) >= 2:
                                        operation = key_parts[0]
                                        operation_counts[operation] = operation_counts.get(operation, 0) + 1
                                        
                                except Exception:
                                    pass  # Skip invalid records
                
                if cursor == 0:
                    break
            
            return {
                "total_records": total_records,
                "status_counts": status_counts,
                "operation_counts": operation_counts,
                "store_type": "redis",
                "key_prefix": self.key_prefix,
                "default_ttl": self.default_ttl
            }
            
        except Exception as e:
            logger.error("Error getting store statistics", error=str(e))
            raise