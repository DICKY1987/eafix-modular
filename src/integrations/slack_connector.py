"""Slack integration for team notifications and collaboration."""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SlackMessage:
    """Slack message representation."""
    channel: str
    text: str
    blocks: Optional[List[Dict]] = None
    thread_ts: Optional[str] = None
    username: Optional[str] = "Workflow Bot"
    icon_emoji: Optional[str] = ":robot_face:"

class SlackConnector:
    """Slack integration connector."""
    
    def __init__(self, bot_token: str, signing_secret: Optional[str] = None):
        self.bot_token = bot_token
        self.signing_secret = signing_secret
        self.base_url = "https://slack.com/api"
        self.session = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {bot_token}",
                "Content-Type": "application/json"
            }
        )
        
    async def test_connection(self) -> Dict[str, Any]:
        """Test Slack connection."""
        try:
            response = await self.session.post(f"{self.base_url}/auth.test")
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return {
                        "status": "connected",
                        "team": data.get("team"),
                        "user": data.get("user"),
                        "bot_id": data.get("bot_id")
                    }
                else:
                    return {"status": "failed", "error": data.get("error")}
            else:
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Slack connection test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def notify_workflow_started(self, channel: str, workflow_id: str, workflow_data: Dict[str, Any]) -> Optional[str]:
        """Send workflow started notification."""
        try:
            blocks = self._build_workflow_started_blocks(workflow_id, workflow_data)
            message = SlackMessage(
                channel=channel,
                text=f"Workflow {workflow_id} has started",
                blocks=blocks
            )
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending workflow started notification: {e}")
            return None
    
    async def notify_workflow_progress(self, channel: str, workflow_id: str, progress_data: Dict[str, Any], thread_ts: Optional[str] = None) -> Optional[str]:
        """Send workflow progress update."""
        try:
            blocks = self._build_progress_blocks(workflow_id, progress_data)
            message = SlackMessage(
                channel=channel,
                text=f"Workflow {workflow_id} progress update",
                blocks=blocks,
                thread_ts=thread_ts
            )
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending progress notification: {e}")
            return None
    
    async def notify_workflow_completed(self, channel: str, workflow_id: str, result_data: Dict[str, Any], thread_ts: Optional[str] = None) -> Optional[str]:
        """Send workflow completion notification."""
        try:
            blocks = self._build_completion_blocks(workflow_id, result_data)
            message = SlackMessage(
                channel=channel,
                text=f"Workflow {workflow_id} completed successfully! :tada:",
                blocks=blocks,
                thread_ts=thread_ts
            )
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending completion notification: {e}")
            return None
    
    async def notify_workflow_failed(self, channel: str, workflow_id: str, error_data: Dict[str, Any], thread_ts: Optional[str] = None) -> Optional[str]:
        """Send workflow failure notification."""
        try:
            blocks = self._build_failure_blocks(workflow_id, error_data)
            message = SlackMessage(
                channel=channel,
                text=f"Workflow {workflow_id} failed :x:",
                blocks=blocks,
                thread_ts=thread_ts,
                icon_emoji=":warning:"
            )
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending failure notification: {e}")
            return None
    
    async def notify_error_recovery(self, channel: str, error_code: str, recovery_action: str, success: bool) -> Optional[str]:
        """Send error recovery notification."""
        try:
            status_emoji = ":white_check_mark:" if success else ":x:"
            status_text = "successful" if success else "failed"
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{status_emoji} *Error Recovery {status_text.title()}*\n*Error:* `{error_code}`\n*Action:* {recovery_action}"
                    }
                }
            ]
            
            message = SlackMessage(
                channel=channel,
                text=f"Error recovery {status_text}",
                blocks=blocks,
                icon_emoji=":gear:"
            )
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending recovery notification: {e}")
            return None
    
    async def notify_cost_alert(self, channel: str, service: str, cost_data: Dict[str, Any]) -> Optional[str]:
        """Send cost alert notification."""
        try:
            current_cost = cost_data.get("current_cost", 0)
            budget_limit = cost_data.get("budget_limit", 0)
            usage_percent = cost_data.get("usage_percent", 0)
            
            warning_level = ":warning:" if usage_percent >= 80 else ":information_source:"
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{warning_level} *Cost Alert - {service}*\n*Current:* ${current_cost:.2f}\n*Budget:* ${budget_limit:.2f}\n*Usage:* {usage_percent:.1f}%"
                    }
                }
            ]
            
            if usage_percent >= 90:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":rotating_light: *Critical:* Approaching budget limit!"
                    }
                })
            
            message = SlackMessage(
                channel=channel,
                text=f"Cost alert for {service}",
                blocks=blocks,
                icon_emoji=":money_with_wings:"
            )
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending cost alert: {e}")
            return None
    
    async def send_message(self, message: SlackMessage) -> Optional[str]:
        """Send message to Slack."""
        try:
            payload = {
                "channel": message.channel,
                "text": message.text,
                "username": message.username,
                "icon_emoji": message.icon_emoji
            }
            
            if message.blocks:
                payload["blocks"] = message.blocks
                
            if message.thread_ts:
                payload["thread_ts"] = message.thread_ts
            
            response = await self.session.post(f"{self.base_url}/chat.postMessage", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data.get("ts")  # Return timestamp for threading
                else:
                    logger.error(f"Slack API error: {data.get('error')}")
                    return None
            else:
                logger.error(f"Slack HTTP error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return None
    
    async def create_workflow_channel(self, workflow_id: str, workflow_name: str) -> Optional[str]:
        """Create dedicated channel for workflow."""
        try:
            channel_name = f"workflow-{workflow_id}"[:21]  # Slack channel name limit
            
            payload = {
                "name": channel_name,
                "is_private": False
            }
            
            response = await self.session.post(f"{self.base_url}/conversations.create", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    channel_id = data.get("channel", {}).get("id")
                    
                    # Set channel topic
                    await self.set_channel_topic(channel_id, f"Workflow: {workflow_name}")
                    
                    return channel_id
                else:
                    logger.error(f"Error creating channel: {data.get('error')}")
                    return None
            return None
            
        except Exception as e:
            logger.error(f"Error creating workflow channel: {e}")
            return None
    
    async def set_channel_topic(self, channel: str, topic: str) -> bool:
        """Set channel topic."""
        try:
            payload = {
                "channel": channel,
                "topic": topic
            }
            
            response = await self.session.post(f"{self.base_url}/conversations.setTopic", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("ok", False)
            return False
            
        except Exception as e:
            logger.error(f"Error setting channel topic: {e}")
            return False
    
    async def invite_users_to_channel(self, channel: str, users: List[str]) -> bool:
        """Invite users to channel."""
        try:
            payload = {
                "channel": channel,
                "users": ",".join(users)
            }
            
            response = await self.session.post(f"{self.base_url}/conversations.invite", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("ok", False)
            return False
            
        except Exception as e:
            logger.error(f"Error inviting users to channel: {e}")
            return False
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information."""
        try:
            response = await self.session.get(f"{self.base_url}/users.info", params={"user": user_id})
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data.get("user")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def _build_workflow_started_blocks(self, workflow_id: str, workflow_data: Dict[str, Any]) -> List[Dict]:
        """Build blocks for workflow started message."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚀 Workflow Started: {workflow_data.get('name', workflow_id)}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Workflow ID:*\n{workflow_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Started:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
        
        if "description" in workflow_data:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{workflow_data['description']}"
                }
            })
        
        if "estimated_duration" in workflow_data:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Estimated Duration:* {workflow_data['estimated_duration']}"
                }
            })
        
        return blocks
    
    def _build_progress_blocks(self, workflow_id: str, progress_data: Dict[str, Any]) -> List[Dict]:
        """Build blocks for progress update message."""
        progress_percent = progress_data.get("overall_progress", 0)
        progress_bar = self._create_progress_bar(progress_percent)
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Workflow Progress Update*\n{progress_bar} {progress_percent}%"
                }
            }
        ]
        
        fields = []
        if "current_phase" in progress_data:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Current Phase:*\n{progress_data['current_phase']}"
            })
        
        if "completed_tasks" in progress_data:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Completed:*\n{progress_data['completed_tasks']} tasks"
            })
        
        if fields:
            blocks.append({
                "type": "section",
                "fields": fields
            })
        
        return blocks
    
    def _build_completion_blocks(self, workflow_id: str, result_data: Dict[str, Any]) -> List[Dict]:
        """Build blocks for completion message."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "✅ Workflow Completed Successfully!"
                }
            }
        ]
        
        fields = []
        if "duration" in result_data:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Duration:*\n{result_data['duration']}"
            })
        
        if "tasks_completed" in result_data:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Tasks:*\n{result_data['tasks_completed']} completed"
            })
        
        if fields:
            blocks.append({
                "type": "section",
                "fields": fields
            })
        
        if "summary" in result_data:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{result_data['summary']}"
                }
            })
        
        return blocks
    
    def _build_failure_blocks(self, workflow_id: str, error_data: Dict[str, Any]) -> List[Dict]:
        """Build blocks for failure message."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "❌ Workflow Failed"
                }
            }
        ]
        
        if "error_message" in error_data:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error:*\n```{error_data['error_message']}```"
                }
            })
        
        fields = []
        if "failed_task" in error_data:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Failed Task:*\n{error_data['failed_task']}"
            })
        
        if "recovery_attempted" in error_data:
            recovery_status = "Yes" if error_data['recovery_attempted'] else "No"
            fields.append({
                "type": "mrkdwn",
                "text": f"*Recovery Attempted:*\n{recovery_status}"
            })
        
        if fields:
            blocks.append({
                "type": "section",
                "fields": fields
            })
        
        return blocks
    
    def _create_progress_bar(self, percent: int, length: int = 20) -> str:
        """Create ASCII progress bar."""
        filled_length = int(length * percent // 100)
        bar = '█' * filled_length + '░' * (length - filled_length)
        return f"[{bar}]"
    
    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose()