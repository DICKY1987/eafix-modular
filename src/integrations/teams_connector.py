"""Microsoft Teams integration for team notifications."""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TeamsCard:
    """Teams adaptive card representation."""
    title: str
    text: str
    color: str = "Good"  # Good, Warning, Attention
    facts: List[Dict[str, str]] = None
    actions: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.facts is None:
            self.facts = []
        if self.actions is None:
            self.actions = []

class TeamsConnector:
    """Microsoft Teams integration connector."""
    
    def __init__(self, webhook_url: Optional[str] = None, app_id: Optional[str] = None, app_password: Optional[str] = None):
        self.webhook_url = webhook_url
        self.app_id = app_id
        self.app_password = app_password
        self.session = httpx.AsyncClient(
            headers={"Content-Type": "application/json"}
        )
        
    async def test_connection(self) -> Dict[str, Any]:
        """Test Teams connection."""
        try:
            if self.webhook_url:
                # Test webhook with a simple ping
                test_card = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "0076D7",
                    "summary": "Connection Test",
                    "sections": [{
                        "activityTitle": "Connection Test",
                        "activitySubtitle": "Testing webhook connectivity",
                        "activityImage": "https://teamsnodesample.azurewebsites.net/static/img/image5.png",
                        "text": "This is a test message to verify the webhook connection."
                    }]
                }
                
                response = await self.session.post(self.webhook_url, json=test_card)
                if response.status_code == 200:
                    return {"status": "connected", "method": "webhook"}
                else:
                    return {"status": "failed", "error": f"Webhook HTTP {response.status_code}"}
            else:
                return {"status": "failed", "error": "No webhook URL configured"}
                
        except Exception as e:
            logger.error(f"Teams connection test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def notify_workflow_started(self, workflow_id: str, workflow_data: Dict[str, Any]) -> bool:
        """Send workflow started notification."""
        try:
            card = self._build_workflow_started_card(workflow_id, workflow_data)
            return await self.send_card(card)
            
        except Exception as e:
            logger.error(f"Error sending workflow started notification: {e}")
            return False
    
    async def notify_workflow_progress(self, workflow_id: str, progress_data: Dict[str, Any]) -> bool:
        """Send workflow progress update."""
        try:
            card = self._build_progress_card(workflow_id, progress_data)
            return await self.send_card(card)
            
        except Exception as e:
            logger.error(f"Error sending progress notification: {e}")
            return False
    
    async def notify_workflow_completed(self, workflow_id: str, result_data: Dict[str, Any]) -> bool:
        """Send workflow completion notification."""
        try:
            card = self._build_completion_card(workflow_id, result_data)
            return await self.send_card(card)
            
        except Exception as e:
            logger.error(f"Error sending completion notification: {e}")
            return False
    
    async def notify_workflow_failed(self, workflow_id: str, error_data: Dict[str, Any]) -> bool:
        """Send workflow failure notification."""
        try:
            card = self._build_failure_card(workflow_id, error_data)
            return await self.send_card(card)
            
        except Exception as e:
            logger.error(f"Error sending failure notification: {e}")
            return False
    
    async def notify_error_recovery(self, error_code: str, recovery_action: str, success: bool) -> bool:
        """Send error recovery notification."""
        try:
            color = "Good" if success else "Attention"
            status_text = "Successful" if success else "Failed"
            
            card_data = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "FF6900" if not success else "00C851",
                "summary": f"Error Recovery {status_text}",
                "sections": [{
                    "activityTitle": f"🔧 Error Recovery {status_text}",
                    "activitySubtitle": f"Error: {error_code}",
                    "facts": [
                        {"name": "Error Code", "value": error_code},
                        {"name": "Recovery Action", "value": recovery_action},
                        {"name": "Status", "value": status_text},
                        {"name": "Timestamp", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    ]
                }]
            }
            
            response = await self.session.post(self.webhook_url, json=card_data)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending recovery notification: {e}")
            return False
    
    async def notify_cost_alert(self, service: str, cost_data: Dict[str, Any]) -> bool:
        """Send cost alert notification."""
        try:
            current_cost = cost_data.get("current_cost", 0)
            budget_limit = cost_data.get("budget_limit", 0)
            usage_percent = cost_data.get("usage_percent", 0)
            
            color = "Attention" if usage_percent >= 80 else "Warning"
            
            card_data = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "FF6900" if usage_percent >= 80 else "FFB900",
                "summary": f"Cost Alert - {service}",
                "sections": [{
                    "activityTitle": f"💰 Cost Alert - {service}",
                    "activitySubtitle": f"Budget usage at {usage_percent:.1f}%",
                    "facts": [
                        {"name": "Service", "value": service},
                        {"name": "Current Cost", "value": f"${current_cost:.2f}"},
                        {"name": "Budget Limit", "value": f"${budget_limit:.2f}"},
                        {"name": "Usage Percentage", "value": f"{usage_percent:.1f}%"},
                        {"name": "Alert Time", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    ]
                }]
            }
            
            if usage_percent >= 90:
                card_data["sections"][0]["text"] = "⚠️ **Critical:** Approaching budget limit!"
            
            response = await self.session.post(self.webhook_url, json=card_data)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending cost alert: {e}")
            return False
    
    async def send_card(self, card: TeamsCard) -> bool:
        """Send adaptive card to Teams."""
        try:
            if not self.webhook_url:
                logger.error("No webhook URL configured")
                return False
                
            card_data = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": self._get_theme_color(card.color),
                "summary": card.title,
                "sections": [{
                    "activityTitle": card.title,
                    "text": card.text,
                    "facts": card.facts
                }]
            }
            
            if card.actions:
                card_data["potentialAction"] = card.actions
            
            response = await self.session.post(self.webhook_url, json=card_data)
            
            if response.status_code == 200:
                logger.info(f"Sent Teams card: {card.title}")
                return True
            else:
                logger.error(f"Failed to send Teams card: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Teams card: {e}")
            return False
    
    async def send_adaptive_card_v2(self, card_payload: Dict[str, Any]) -> bool:
        """Send Adaptive Card v2 format."""
        try:
            if not self.webhook_url:
                logger.error("No webhook URL configured")
                return False
                
            response = await self.session.post(self.webhook_url, json=card_payload)
            
            if response.status_code == 200:
                logger.info("Sent adaptive card v2")
                return True
            else:
                logger.error(f"Failed to send adaptive card: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending adaptive card: {e}")
            return False
    
    def _build_workflow_started_card(self, workflow_id: str, workflow_data: Dict[str, Any]) -> TeamsCard:
        """Build card for workflow started notification."""
        facts = [
            {"name": "Workflow ID", "value": workflow_id},
            {"name": "Started", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        ]
        
        if "description" in workflow_data:
            facts.append({"name": "Description", "value": workflow_data["description"]})
        
        if "estimated_duration" in workflow_data:
            facts.append({"name": "Estimated Duration", "value": workflow_data["estimated_duration"]})
        
        if "tasks" in workflow_data:
            facts.append({"name": "Total Tasks", "value": str(len(workflow_data["tasks"]))})
        
        return TeamsCard(
            title=f"🚀 Workflow Started: {workflow_data.get('name', workflow_id)}",
            text="A new workflow has been initiated and is now running.",
            color="Good",
            facts=facts
        )
    
    def _build_progress_card(self, workflow_id: str, progress_data: Dict[str, Any]) -> TeamsCard:
        """Build card for progress update."""
        progress_percent = progress_data.get("overall_progress", 0)
        progress_bar = self._create_progress_bar(progress_percent)
        
        facts = [
            {"name": "Progress", "value": f"{progress_bar} {progress_percent}%"}
        ]
        
        if "current_phase" in progress_data:
            facts.append({"name": "Current Phase", "value": progress_data["current_phase"]})
        
        if "completed_tasks" in progress_data:
            facts.append({"name": "Completed Tasks", "value": str(progress_data["completed_tasks"])})
        
        if "remaining_tasks" in progress_data:
            facts.append({"name": "Remaining Tasks", "value": str(progress_data["remaining_tasks"])})
        
        if "next_action" in progress_data:
            facts.append({"name": "Next Action", "value": progress_data["next_action"]})
        
        facts.append({"name": "Updated", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        
        color = "Good" if progress_percent >= 50 else "Warning"
        
        return TeamsCard(
            title=f"📊 Workflow Progress Update",
            text=f"Workflow {workflow_id} is {progress_percent}% complete.",
            color=color,
            facts=facts
        )
    
    def _build_completion_card(self, workflow_id: str, result_data: Dict[str, Any]) -> TeamsCard:
        """Build card for workflow completion."""
        facts = [
            {"name": "Status", "value": "✅ Completed Successfully"},
            {"name": "Completed", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        ]
        
        if "duration" in result_data:
            facts.append({"name": "Total Duration", "value": result_data["duration"]})
        
        if "tasks_completed" in result_data:
            facts.append({"name": "Tasks Completed", "value": str(result_data["tasks_completed"])})
        
        if "files_modified" in result_data:
            facts.append({"name": "Files Modified", "value": str(result_data["files_modified"])})
        
        text = f"Workflow {workflow_id} has completed successfully! 🎉"
        if "summary" in result_data:
            text += f"\n\n**Summary:** {result_data['summary']}"
        
        return TeamsCard(
            title="✅ Workflow Completed Successfully",
            text=text,
            color="Good",
            facts=facts
        )
    
    def _build_failure_card(self, workflow_id: str, error_data: Dict[str, Any]) -> TeamsCard:
        """Build card for workflow failure."""
        facts = [
            {"name": "Status", "value": "❌ Failed"},
            {"name": "Failed", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        ]
        
        if "failed_task" in error_data:
            facts.append({"name": "Failed Task", "value": error_data["failed_task"]})
        
        if "recovery_attempted" in error_data:
            recovery_status = "Yes" if error_data["recovery_attempted"] else "No"
            facts.append({"name": "Recovery Attempted", "value": recovery_status})
        
        text = f"Workflow {workflow_id} has failed and requires attention."
        if "error_message" in error_data:
            text += f"\n\n**Error:** {error_data['error_message']}"
        
        return TeamsCard(
            title="❌ Workflow Failed",
            text=text,
            color="Attention",
            facts=facts
        )
    
    def _get_theme_color(self, color: str) -> str:
        """Get theme color hex code."""
        color_map = {
            "Good": "00C851",
            "Warning": "FFB900", 
            "Attention": "FF6900"
        }
        return color_map.get(color, "0076D7")
    
    def _create_progress_bar(self, percent: int, length: int = 10) -> str:
        """Create Unicode progress bar."""
        filled_length = int(length * percent // 100)
        bar = '█' * filled_length + '░' * (length - filled_length)
        return bar
    
    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose()