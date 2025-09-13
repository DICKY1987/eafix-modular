"""Integration manager for coordinating enterprise connectors."""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime, timedelta

from .jira_connector import JiraConnector, JiraIssue
from .slack_connector import SlackConnector
from .github_connector import GitHubConnector
from .teams_connector import TeamsConnector

logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    """Supported integration types."""
    JIRA = "jira"
    SLACK = "slack"
    GITHUB = "github"
    TEAMS = "teams"
    CONFLUENCE = "confluence"

@dataclass
class IntegrationConfig:
    """Integration configuration."""
    integration_type: IntegrationType
    enabled: bool
    config: Dict[str, Any]
    channels: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    rate_limit: Optional[int] = None
    retry_count: int = 3

@dataclass
class WorkflowIntegrationContext:
    """Context for workflow-specific integrations."""
    workflow_id: str
    workflow_name: str
    user_id: Optional[str] = None
    project_key: Optional[str] = None
    slack_channel: Optional[str] = None
    github_repo: Optional[str] = None
    jira_issue_key: Optional[str] = None
    teams_thread_id: Optional[str] = None
    created_resources: Set[str] = field(default_factory=set)

class IntegrationManager:
    """Manages all enterprise integrations."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.integrations: Dict[IntegrationType, Any] = {}
        self.configs: Dict[IntegrationType, IntegrationConfig] = {}
        self.workflow_contexts: Dict[str, WorkflowIntegrationContext] = {}
        self.rate_limiters: Dict[str, List[datetime]] = {}
        
        if config_file:
            self.load_config(config_file)
    
    def load_config(self, config_file: str):
        """Load integration configurations from file."""
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            for integration_name, config in config_data.get("integrations", {}).items():
                try:
                    integration_type = IntegrationType(integration_name)
                    self.configs[integration_type] = IntegrationConfig(
                        integration_type=integration_type,
                        enabled=config.get("enabled", False),
                        config=config.get("config", {}),
                        channels=config.get("channels", []),
                        filters=config.get("filters", {}),
                        rate_limit=config.get("rate_limit"),
                        retry_count=config.get("retry_count", 3)
                    )
                except ValueError:
                    logger.warning(f"Unknown integration type: {integration_name}")
                    
        except Exception as e:
            logger.error(f"Error loading integration config: {e}")
    
    async def initialize_integrations(self):
        """Initialize all enabled integrations."""
        for integration_type, config in self.configs.items():
            if not config.enabled:
                continue
                
            try:
                connector = await self._create_connector(integration_type, config.config)
                if connector:
                    # Test connection
                    test_result = await connector.test_connection()
                    if test_result.get("status") == "connected":
                        self.integrations[integration_type] = connector
                        logger.info(f"Initialized {integration_type.value} integration")
                    else:
                        logger.error(f"Failed to connect to {integration_type.value}: {test_result.get('error')}")
                        
            except Exception as e:
                logger.error(f"Error initializing {integration_type.value}: {e}")
    
    async def create_workflow_context(self, workflow_id: str, workflow_data: Dict[str, Any]) -> WorkflowIntegrationContext:
        """Create integration context for workflow."""
        context = WorkflowIntegrationContext(
            workflow_id=workflow_id,
            workflow_name=workflow_data.get("name", workflow_id),
            user_id=workflow_data.get("user_id"),
            project_key=workflow_data.get("jira_project"),
            slack_channel=workflow_data.get("slack_channel"),
            github_repo=workflow_data.get("github_repo")
        )
        
        self.workflow_contexts[workflow_id] = context
        
        # Create workflow-specific resources
        await self._create_workflow_resources(context, workflow_data)
        
        return context
    
    async def notify_workflow_started(self, workflow_id: str, workflow_data: Dict[str, Any]):
        """Notify all integrations about workflow start."""
        context = await self.create_workflow_context(workflow_id, workflow_data)
        
        # Parallel notifications
        tasks = []
        
        # JIRA: Create issue
        if IntegrationType.JIRA in self.integrations and context.project_key:
            tasks.append(self._create_jira_issue(context, workflow_data))
        
        # Slack: Send notification
        if IntegrationType.SLACK in self.integrations and context.slack_channel:
            tasks.append(self._notify_slack_started(context, workflow_data))
        
        # GitHub: Create discussion or comment
        if IntegrationType.GITHUB in self.integrations and context.github_repo:
            tasks.append(self._notify_github_started(context, workflow_data))
        
        # Teams: Send notification
        if IntegrationType.TEAMS in self.integrations:
            tasks.append(self._notify_teams_started(context, workflow_data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def notify_workflow_progress(self, workflow_id: str, progress_data: Dict[str, Any]):
        """Notify all integrations about workflow progress."""
        if workflow_id not in self.workflow_contexts:
            logger.warning(f"No context found for workflow {workflow_id}")
            return
        
        context = self.workflow_contexts[workflow_id]
        
        # Rate limit progress updates
        if not self._check_rate_limit(f"progress:{workflow_id}", 60):  # Max 1 update per minute
            return
        
        # Parallel notifications
        tasks = []
        
        # JIRA: Update issue
        if IntegrationType.JIRA in self.integrations and context.jira_issue_key:
            tasks.append(self._update_jira_progress(context, progress_data))
        
        # Slack: Send progress update
        if IntegrationType.SLACK in self.integrations and context.slack_channel:
            tasks.append(self._notify_slack_progress(context, progress_data))
        
        # GitHub: Update discussion or add comment
        if IntegrationType.GITHUB in self.integrations and context.github_repo:
            tasks.append(self._notify_github_progress(context, progress_data))
        
        # Teams: Send progress update
        if IntegrationType.TEAMS in self.integrations and context.teams_thread_id:
            tasks.append(self._notify_teams_progress(context, progress_data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def notify_workflow_completed(self, workflow_id: str, result_data: Dict[str, Any]):
        """Notify all integrations about workflow completion."""
        if workflow_id not in self.workflow_contexts:
            logger.warning(f"No context found for workflow {workflow_id}")
            return
        
        context = self.workflow_contexts[workflow_id]
        
        # Parallel notifications
        tasks = []
        
        # JIRA: Complete issue
        if IntegrationType.JIRA in self.integrations and context.jira_issue_key:
            tasks.append(self._complete_jira_issue(context, result_data))
        
        # Slack: Send completion notification
        if IntegrationType.SLACK in self.integrations and context.slack_channel:
            tasks.append(self._notify_slack_completed(context, result_data))
        
        # GitHub: Close discussion or add final comment
        if IntegrationType.GITHUB in self.integrations and context.github_repo:
            tasks.append(self._notify_github_completed(context, result_data))
        
        # Teams: Send completion notification
        if IntegrationType.TEAMS in self.integrations and context.teams_thread_id:
            tasks.append(self._notify_teams_completed(context, result_data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Clean up context
        del self.workflow_contexts[workflow_id]
    
    async def notify_workflow_failed(self, workflow_id: str, error_data: Dict[str, Any]):
        """Notify all integrations about workflow failure."""
        if workflow_id not in self.workflow_contexts:
            logger.warning(f"No context found for workflow {workflow_id}")
            return
        
        context = self.workflow_contexts[workflow_id]
        
        # Parallel notifications
        tasks = []
        
        # JIRA: Report failure
        if IntegrationType.JIRA in self.integrations and context.jira_issue_key:
            tasks.append(self._report_jira_failure(context, error_data))
        
        # Slack: Send failure notification
        if IntegrationType.SLACK in self.integrations and context.slack_channel:
            tasks.append(self._notify_slack_failed(context, error_data))
        
        # GitHub: Add failure comment
        if IntegrationType.GITHUB in self.integrations and context.github_repo:
            tasks.append(self._notify_github_failed(context, error_data))
        
        # Teams: Send failure notification
        if IntegrationType.TEAMS in self.integrations and context.teams_thread_id:
            tasks.append(self._notify_teams_failed(context, error_data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def notify_error_recovery(self, error_code: str, recovery_action: str, success: bool):
        """Notify about error recovery attempts."""
        # Rate limit recovery notifications
        if not self._check_rate_limit("error_recovery", 300):  # Max 1 every 5 minutes
            return
        
        # Broadcast to all configured channels
        tasks = []
        
        if IntegrationType.SLACK in self.integrations:
            slack = self.integrations[IntegrationType.SLACK]
            for channel in self.configs[IntegrationType.SLACK].channels:
                tasks.append(slack.notify_error_recovery(channel, error_code, recovery_action, success))
        
        if IntegrationType.TEAMS in self.integrations:
            teams = self.integrations[IntegrationType.TEAMS]
            tasks.append(teams.notify_error_recovery(error_code, recovery_action, success))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def notify_cost_alert(self, service: str, cost_data: Dict[str, Any]):
        """Notify about cost alerts."""
        # Rate limit cost alerts
        if not self._check_rate_limit(f"cost_alert:{service}", 1800):  # Max 1 every 30 minutes
            return
        
        tasks = []
        
        if IntegrationType.SLACK in self.integrations:
            slack = self.integrations[IntegrationType.SLACK]
            for channel in self.configs[IntegrationType.SLACK].channels:
                tasks.append(slack.notify_cost_alert(channel, service, cost_data))
        
        if IntegrationType.TEAMS in self.integrations:
            teams = self.integrations[IntegrationType.TEAMS]
            tasks.append(teams.notify_cost_alert(service, cost_data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all integrations."""
        status = {}
        
        for integration_type, config in self.configs.items():
            status[integration_type.value] = {
                "enabled": config.enabled,
                "connected": integration_type in self.integrations,
                "channels": len(config.channels),
                "rate_limit": config.rate_limit
            }
        
        return {
            "integrations": status,
            "active_workflows": len(self.workflow_contexts)
        }
    
    async def _create_connector(self, integration_type: IntegrationType, config: Dict[str, Any]):
        """Create connector instance."""
        if integration_type == IntegrationType.JIRA:
            return JiraConnector(
                base_url=config["base_url"],
                username=config["username"], 
                api_token=config["api_token"]
            )
        elif integration_type == IntegrationType.SLACK:
            return SlackConnector(
                bot_token=config["bot_token"],
                signing_secret=config.get("signing_secret")
            )
        elif integration_type == IntegrationType.GITHUB:
            return GitHubConnector(
                token=config["token"],
                organization=config.get("organization")
            )
        elif integration_type == IntegrationType.TEAMS:
            return TeamsConnector(
                webhook_url=config.get("webhook_url"),
                app_id=config.get("app_id"),
                app_password=config.get("app_password")
            )
        
        return None
    
    async def _create_workflow_resources(self, context: WorkflowIntegrationContext, workflow_data: Dict[str, Any]):
        """Create workflow-specific resources."""
        try:
            # Create dedicated Slack channel if needed
            if (IntegrationType.SLACK in self.integrations and 
                workflow_data.get("create_slack_channel")):
                slack = self.integrations[IntegrationType.SLACK]
                channel_id = await slack.create_workflow_channel(
                    context.workflow_id, 
                    context.workflow_name
                )
                if channel_id:
                    context.slack_channel = channel_id
                    context.created_resources.add(f"slack_channel:{channel_id}")
                    
        except Exception as e:
            logger.error(f"Error creating workflow resources: {e}")
    
    async def _create_jira_issue(self, context: WorkflowIntegrationContext, workflow_data: Dict[str, Any]):
        """Create JIRA issue for workflow."""
        try:
            jira = self.integrations[IntegrationType.JIRA]
            issue = await jira.create_workflow_issue(
                context.workflow_id,
                workflow_data,
                context.project_key
            )
            if issue:
                context.jira_issue_key = issue.key
                
        except Exception as e:
            logger.error(f"Error creating JIRA issue: {e}")
    
    async def _notify_slack_started(self, context: WorkflowIntegrationContext, workflow_data: Dict[str, Any]):
        """Send Slack started notification."""
        try:
            slack = self.integrations[IntegrationType.SLACK]
            await slack.notify_workflow_started(
                context.slack_channel,
                context.workflow_id,
                workflow_data
            )
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
    
    async def _update_jira_progress(self, context: WorkflowIntegrationContext, progress_data: Dict[str, Any]):
        """Update JIRA issue progress."""
        try:
            jira = self.integrations[IntegrationType.JIRA]
            await jira.update_issue_progress(context.jira_issue_key, progress_data)
        except Exception as e:
            logger.error(f"Error updating JIRA progress: {e}")
    
    async def _notify_slack_progress(self, context: WorkflowIntegrationContext, progress_data: Dict[str, Any]):
        """Send Slack progress notification."""
        try:
            slack = self.integrations[IntegrationType.SLACK]
            await slack.notify_workflow_progress(
                context.slack_channel,
                context.workflow_id,
                progress_data
            )
        except Exception as e:
            logger.error(f"Error sending Slack progress: {e}")
    
    def _check_rate_limit(self, key: str, interval_seconds: int) -> bool:
        """Check if action is within rate limit."""
        now = datetime.now()
        
        if key not in self.rate_limiters:
            self.rate_limiters[key] = []
        
        # Clean old entries
        cutoff = now - timedelta(seconds=interval_seconds)
        self.rate_limiters[key] = [
            timestamp for timestamp in self.rate_limiters[key] 
            if timestamp > cutoff
        ]
        
        # Check if we can proceed
        if len(self.rate_limiters[key]) == 0:
            self.rate_limiters[key].append(now)
            return True
        
        return False
    
    async def close(self):
        """Close all integration connections."""
        for connector in self.integrations.values():
            try:
                if hasattr(connector, 'close'):
                    await connector.close()
            except Exception as e:
                logger.error(f"Error closing connector: {e}")

# Global integration manager instance
integration_manager = IntegrationManager()