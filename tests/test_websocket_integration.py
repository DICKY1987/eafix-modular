"""
Integration tests for WebSocket and enterprise integration features.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch

from src.websocket.connection_manager import ConnectionManager
from src.websocket.event_broadcaster import EventBroadcaster, EventType
from src.websocket.auth_middleware import WebSocketAuthMiddleware
from src.integrations.integration_manager import IntegrationManager, IntegrationType


@pytest.fixture
def connection_manager():
    """Create connection manager for testing."""
    return ConnectionManager("redis://localhost:6379/9")  # Test database


@pytest.fixture
def event_broadcaster():
    """Create event broadcaster for testing."""
    return EventBroadcaster("redis://localhost:6379/9")


@pytest.fixture
def auth_middleware():
    """Create auth middleware for testing."""
    return WebSocketAuthMiddleware("test-secret-key", "redis://localhost:6379/9")


@pytest.fixture
def integration_manager():
    """Create integration manager for testing."""
    return IntegrationManager()


class TestConnectionManager:
    """Test WebSocket connection management."""
    
    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, connection_manager):
        """Test connection creation and cleanup."""
        # Mock WebSocket
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        # Test connection
        client_id = await connection_manager.connect(mock_websocket)
        assert client_id in connection_manager.connections
        
        # Test disconnection
        await connection_manager.disconnect(client_id)
        assert client_id not in connection_manager.connections
        
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_subscription_management(self, connection_manager):
        """Test topic subscription and unsubscription."""
        # Mock WebSocket
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        # Create connection
        client_id = await connection_manager.connect(mock_websocket)
        
        # Test subscription
        topics = ["workflow.events", "system.health"]
        success = await connection_manager.subscribe(client_id, topics)
        assert success
        
        connection = connection_manager.connections[client_id]
        assert "workflow.events" in connection.subscriptions
        assert "system.health" in connection.subscriptions
        
        # Test unsubscription
        await connection_manager.unsubscribe(client_id, ["workflow.events"])
        assert "workflow.events" not in connection.subscriptions
        assert "system.health" in connection.subscriptions
        
        # Cleanup
        await connection_manager.disconnect(client_id)
    
    @pytest.mark.asyncio
    async def test_message_broadcasting(self, connection_manager):
        """Test message broadcasting to topics."""
        # Mock WebSocket
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        # Create connection and subscribe
        client_id = await connection_manager.connect(mock_websocket)
        await connection_manager.subscribe(client_id, ["test.topic"])
        
        # Test broadcasting
        message = {"type": "test", "data": "hello"}
        sent_count = await connection_manager.broadcast_to_topic("test.topic", message)
        assert sent_count == 1
        
        mock_websocket.send_text.assert_called_with(json.dumps(message))
        
        # Cleanup
        await connection_manager.disconnect(client_id)
    
    def test_connection_stats(self, connection_manager):
        """Test connection statistics."""
        stats = connection_manager.get_connection_stats()
        
        assert "total_connections" in stats
        assert "unique_users" in stats
        assert "topics" in stats
        assert "connections_by_topic" in stats


class TestEventBroadcaster:
    """Test event broadcasting system."""
    
    @pytest.mark.asyncio
    async def test_workflow_events(self, event_broadcaster):
        """Test workflow event broadcasting."""
        workflow_id = "test-workflow-123"
        workflow_data = {"name": "Test Workflow", "description": "A test workflow"}
        
        # Mock connection manager
        with patch('src.websocket.event_broadcaster.connection_manager') as mock_cm:
            mock_cm.broadcast_to_topic = AsyncMock(return_value=1)
            mock_cm.broadcast_to_all = AsyncMock(return_value=1)
            
            # Test workflow started event
            await event_broadcaster.broadcast_workflow_started(workflow_id, workflow_data)
            
            # Verify broadcast calls
            mock_cm.broadcast_to_topic.assert_called()
            
            # Test workflow progress event
            progress_data = {"overall_progress": 50, "current_phase": "Processing"}
            await event_broadcaster.broadcast_workflow_progress(workflow_id, progress_data)
            
            # Test workflow completion event
            result_data = {"duration": "5 minutes", "tasks_completed": 3}
            await event_broadcaster.broadcast_workflow_completed(workflow_id, result_data)
            
            # Test workflow failure event
            error_data = {"error_message": "Task failed", "failed_task": "process_data"}
            await event_broadcaster.broadcast_workflow_failed(workflow_id, error_data)
    
    @pytest.mark.asyncio
    async def test_system_events(self, event_broadcaster):
        """Test system-level event broadcasting."""
        with patch('src.websocket.event_broadcaster.connection_manager') as mock_cm:
            mock_cm.broadcast_to_all = AsyncMock(return_value=1)
            
            # Test system health event
            health_data = {"cpu_usage": 45, "memory_usage": 60, "disk_space": 80}
            await event_broadcaster.broadcast_system_health(health_data)
            
            # Test notification event
            await event_broadcaster.broadcast_notification("System maintenance scheduled", "warning")
            
            # Test error recovery event
            await event_broadcaster.broadcast_error_recovery("ERR_DISK_SPACE", "cleaned temp files", {"recovered": True})
            
            # Test cost alert
            cost_data = {"current_cost": 50.0, "budget_limit": 100.0, "usage_percent": 50.0}
            await event_broadcaster.broadcast_cost_alert("claude", cost_data)
    
    def test_event_history(self, event_broadcaster):
        """Test event history management."""
        # Add some test events to history
        from datetime import datetime
        from src.websocket.event_broadcaster import WorkflowEvent
        
        test_event = WorkflowEvent(
            event_type=EventType.WORKFLOW_STARTED,
            workflow_id="test-workflow",
            timestamp=datetime.now(),
            data={"test": "data"}
        )
        
        event_broadcaster.event_history.append(test_event)
        
        # Test recent events retrieval
        recent_events = event_broadcaster.get_recent_events()
        assert len(recent_events) > 0
        
        # Test filtered events
        workflow_events = event_broadcaster.get_recent_events(workflow_id="test-workflow")
        assert len(workflow_events) > 0
        
        type_events = event_broadcaster.get_recent_events(event_type=EventType.WORKFLOW_STARTED)
        assert len(type_events) > 0


class TestAuthMiddleware:
    """Test WebSocket authentication middleware."""
    
    @pytest.mark.asyncio
    async def test_token_authentication(self, auth_middleware):
        """Test JWT token authentication."""
        # Generate test token
        token = auth_middleware.generate_token("test_user", "Test User", ["user"], ["read"])
        
        # Test authentication
        user_info = await auth_middleware.authenticate_token(token)
        assert user_info is not None
        assert user_info["user_id"] == "test_user"
        assert user_info["username"] == "Test User"
        assert "user" in user_info["roles"]
        assert "read" in user_info["permissions"]
    
    @pytest.mark.asyncio
    async def test_api_key_authentication(self, auth_middleware):
        """Test API key authentication."""
        # Create test API key
        api_key = await auth_middleware.create_api_key("test_user", "Test User", ["user"], ["read"])
        
        # Test authentication
        user_info = await auth_middleware.authenticate_api_key(api_key)
        assert user_info is not None
        assert user_info["user_id"] == "test_user"
        assert user_info["username"] == "Test User"
    
    @pytest.mark.asyncio
    async def test_session_authentication(self, auth_middleware):
        """Test session authentication."""
        # Create test session
        session_id = await auth_middleware.create_session("test_user", "Test User", ["user"], ["read"])
        
        # Test authentication
        user_info = await auth_middleware.authenticate_session(session_id)
        assert user_info is not None
        assert user_info["user_id"] == "test_user"
        assert user_info["username"] == "Test User"
    
    @pytest.mark.asyncio
    async def test_invalid_authentication(self, auth_middleware):
        """Test invalid authentication scenarios."""
        # Test invalid token
        user_info = await auth_middleware.authenticate_token("invalid_token")
        assert user_info is None
        
        # Test invalid API key
        user_info = await auth_middleware.authenticate_api_key("invalid_key")
        assert user_info is None
        
        # Test invalid session
        user_info = await auth_middleware.authenticate_session("invalid_session")
        assert user_info is None
    
    def test_permission_checking(self, auth_middleware):
        """Test permission and role checking."""
        user_info = {
            "user_id": "test_user",
            "roles": ["user", "developer"],
            "permissions": ["read", "write"]
        }
        
        # Test permission checking
        assert auth_middleware.check_permission(user_info, "read")
        assert auth_middleware.check_permission(user_info, "write")
        assert not auth_middleware.check_permission(user_info, "admin")
        
        # Test role checking
        assert auth_middleware.check_role(user_info, "user")
        assert auth_middleware.check_role(user_info, "developer")
        assert not auth_middleware.check_role(user_info, "admin")
        
        # Test admin role (should have all permissions)
        admin_user = {
            "user_id": "admin_user",
            "roles": ["admin"],
            "permissions": []
        }
        
        assert auth_middleware.check_permission(admin_user, "any_permission")


class TestIntegrationManager:
    """Test enterprise integration management."""
    
    def test_config_loading(self, integration_manager):
        """Test integration configuration loading."""
        # Create test config
        test_config = {
            "integrations": {
                "slack": {
                    "enabled": True,
                    "config": {"bot_token": "test_token"},
                    "channels": ["#test"],
                    "rate_limit": 60
                }
            }
        }
        
        # Write test config to temp file
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            config_file = f.name
        
        try:
            # Load config
            integration_manager.load_config(config_file)
            
            # Verify config loaded
            assert IntegrationType.SLACK in integration_manager.configs
            config = integration_manager.configs[IntegrationType.SLACK]
            assert config.enabled
            assert config.config["bot_token"] == "test_token"
            assert "#test" in config.channels
            assert config.rate_limit == 60
            
        finally:
            import os
            os.unlink(config_file)
    
    def test_integration_status(self, integration_manager):
        """Test integration status reporting."""
        status = integration_manager.get_integration_status()
        
        assert "integrations" in status
        assert "active_workflows" in status
    
    @pytest.mark.asyncio
    async def test_workflow_context_creation(self, integration_manager):
        """Test workflow integration context creation."""
        workflow_id = "test-workflow-123"
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow",
            "user_id": "test_user",
            "jira_project": "TEST",
            "slack_channel": "#workflows"
        }
        
        # Create context
        context = await integration_manager.create_workflow_context(workflow_id, workflow_data)
        
        assert context.workflow_id == workflow_id
        assert context.workflow_name == "Test Workflow"
        assert context.user_id == "test_user"
        assert context.project_key == "TEST"
        assert context.slack_channel == "#workflows"
        
        # Verify context stored
        assert workflow_id in integration_manager.workflow_contexts
    
    def test_rate_limiting(self, integration_manager):
        """Test rate limiting functionality."""
        # Test rate limit check
        key = "test_operation"
        interval = 60  # 60 seconds
        
        # First call should pass
        assert integration_manager._check_rate_limit(key, interval)
        
        # Immediate second call should fail
        assert not integration_manager._check_rate_limit(key, interval)


@pytest.mark.asyncio
async def test_integration_workflow():
    """Test complete integration workflow."""
    # This is a higher-level integration test
    connection_manager = ConnectionManager("redis://localhost:6379/9")
    event_broadcaster = EventBroadcaster("redis://localhost:6379/9")
    
    # Mock WebSocket connection
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    
    try:
        # Create connection and subscribe to workflow events
        client_id = await connection_manager.connect(mock_websocket, "test_user")
        await connection_manager.subscribe(client_id, ["workflow:test-123", "events:workflow.progress"])
        
        # Simulate workflow events
        workflow_id = "test-123"
        
        # Start workflow
        await event_broadcaster.broadcast_workflow_started(
            workflow_id,
            {"name": "Test Workflow", "description": "Integration test workflow"}
        )
        
        # Progress update
        await event_broadcaster.broadcast_workflow_progress(
            workflow_id,
            {"overall_progress": 50, "current_phase": "Processing", "completed_tasks": 2}
        )
        
        # Complete workflow
        await event_broadcaster.broadcast_workflow_completed(
            workflow_id,
            {"duration": "2 minutes", "tasks_completed": 4, "summary": "All tasks completed successfully"}
        )
        
        # Verify WebSocket calls were made
        assert mock_websocket.send_text.call_count >= 3
        
    finally:
        # Cleanup
        await connection_manager.disconnect(client_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])