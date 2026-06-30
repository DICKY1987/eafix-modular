"""JIRA integration for automated issue tracking."""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class JiraIssue:
    """JIRA issue representation."""
    key: str
    summary: str
    description: str
    status: str
    assignee: Optional[str] = None
    priority: str = "Medium"
    labels: List[str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []

class JiraConnector:
    """JIRA integration connector."""
    
    def __init__(self, base_url: str, username: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.session = httpx.AsyncClient(
            auth=(username, api_token),
            headers={"Accept": "application/json", "Content-Type": "application/json"}
        )
        
    async def test_connection(self) -> Dict[str, Any]:
        """Test JIRA connection."""
        try:
            response = await self.session.get(f"{self.base_url}/rest/api/3/myself")
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "status": "connected",
                    "user": user_data.get("displayName"),
                    "email": user_data.get("emailAddress")
                }
            else:
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"JIRA connection test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def create_workflow_issue(self, workflow_id: str, workflow_data: Dict[str, Any], project_key: str) -> Optional[JiraIssue]:
        """Create JIRA issue for workflow execution."""
        try:
            issue_data = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": f"Workflow Execution: {workflow_data.get('name', workflow_id)}",
                    "description": self._format_workflow_description(workflow_id, workflow_data),
                    "issuetype": {"name": "Task"},
                    "priority": {"name": self._get_priority_from_workflow(workflow_data)},
                    "labels": ["automation", "workflow", f"workflow-{workflow_id}"]
                }
            }
            
            # Add assignee if specified
            assignee = workflow_data.get("assignee")
            if assignee:
                issue_data["fields"]["assignee"] = {"name": assignee}
            
            response = await self.session.post(
                f"{self.base_url}/rest/api/3/issue",
                json=issue_data
            )
            
            if response.status_code == 201:
                result = response.json()
                issue_key = result["key"]
                logger.info(f"Created JIRA issue {issue_key} for workflow {workflow_id}")
                
                return JiraIssue(
                    key=issue_key,
                    summary=issue_data["fields"]["summary"],
                    description=issue_data["fields"]["description"],
                    status="To Do",
                    assignee=assignee,
                    priority=issue_data["fields"]["priority"]["name"],
                    labels=issue_data["fields"]["labels"]
                )
            else:
                logger.error(f"Failed to create JIRA issue: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating JIRA issue for workflow {workflow_id}: {e}")
            return None
    
    async def update_issue_progress(self, issue_key: str, progress_data: Dict[str, Any]) -> bool:
        """Update JIRA issue with workflow progress."""
        try:
            # Add comment with progress update
            comment_data = {
                "body": self._format_progress_comment(progress_data)
            }
            
            response = await self.session.post(
                f"{self.base_url}/rest/api/3/issue/{issue_key}/comment",
                json=comment_data
            )
            
            if response.status_code == 201:
                # Update custom fields if available
                await self._update_custom_fields(issue_key, progress_data)
                logger.info(f"Updated JIRA issue {issue_key} with progress")
                return True
            else:
                logger.error(f"Failed to update JIRA issue {issue_key}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating JIRA issue {issue_key}: {e}")
            return False
    
    async def complete_workflow_issue(self, issue_key: str, result_data: Dict[str, Any]) -> bool:
        """Mark JIRA issue as complete with results."""
        try:
            # Transition issue to Done
            transitions = await self._get_issue_transitions(issue_key)
            done_transition = None
            
            for transition in transitions:
                if transition["name"].lower() in ["done", "complete", "resolved"]:
                    done_transition = transition
                    break
            
            if done_transition:
                await self._transition_issue(issue_key, done_transition["id"])
            
            # Add completion comment
            comment_data = {
                "body": self._format_completion_comment(result_data)
            }
            
            response = await self.session.post(
                f"{self.base_url}/rest/api/3/issue/{issue_key}/comment",
                json=comment_data
            )
            
            logger.info(f"Completed JIRA issue {issue_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing JIRA issue {issue_key}: {e}")
            return False
    
    async def report_workflow_failure(self, issue_key: str, error_data: Dict[str, Any]) -> bool:
        """Report workflow failure in JIRA issue."""
        try:
            # Add failure comment
            comment_data = {
                "body": self._format_failure_comment(error_data)
            }
            
            response = await self.session.post(
                f"{self.base_url}/rest/api/3/issue/{issue_key}/comment",
                json=comment_data
            )
            
            # Set priority to High for failures
            update_data = {
                "fields": {
                    "priority": {"name": "High"}
                }
            }
            
            await self.session.put(
                f"{self.base_url}/rest/api/3/issue/{issue_key}",
                json=update_data
            )
            
            logger.info(f"Reported failure for JIRA issue {issue_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error reporting failure for JIRA issue {issue_key}: {e}")
            return False
    
    async def get_project_info(self, project_key: str) -> Optional[Dict[str, Any]]:
        """Get project information."""
        try:
            response = await self.session.get(f"{self.base_url}/rest/api/3/project/{project_key}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting project info for {project_key}: {e}")
            return None
    
    async def search_issues(self, jql: str, fields: List[str] = None) -> List[Dict[str, Any]]:
        """Search JIRA issues using JQL."""
        try:
            params = {"jql": jql}
            if fields:
                params["fields"] = ",".join(fields)
            
            response = await self.session.get(
                f"{self.base_url}/rest/api/3/search",
                params=params
            )
            
            if response.status_code == 200:
                return response.json().get("issues", [])
            return []
            
        except Exception as e:
            logger.error(f"Error searching JIRA issues: {e}")
            return []
    
    def _format_workflow_description(self, workflow_id: str, workflow_data: Dict[str, Any]) -> str:
        """Format workflow description for JIRA."""
        description = f"*Automated Workflow Execution*\n\n"
        description += f"*Workflow ID:* {workflow_id}\n"
        description += f"*Started:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if "description" in workflow_data:
            description += f"*Description:* {workflow_data['description']}\n"
        
        if "tasks" in workflow_data:
            description += f"*Tasks:* {len(workflow_data['tasks'])}\n"
        
        if "estimated_duration" in workflow_data:
            description += f"*Estimated Duration:* {workflow_data['estimated_duration']}\n"
        
        description += "\n*Progress will be updated automatically as the workflow executes.*"
        
        return description
    
    def _format_progress_comment(self, progress_data: Dict[str, Any]) -> str:
        """Format progress update comment."""
        comment = f"*Workflow Progress Update* - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if "overall_progress" in progress_data:
            comment += f"*Overall Progress:* {progress_data['overall_progress']}%\n"
        
        if "current_phase" in progress_data:
            comment += f"*Current Phase:* {progress_data['current_phase']}\n"
        
        if "completed_tasks" in progress_data:
            comment += f"*Completed Tasks:* {progress_data['completed_tasks']}\n"
        
        if "remaining_tasks" in progress_data:
            comment += f"*Remaining Tasks:* {progress_data['remaining_tasks']}\n"
        
        if "next_action" in progress_data:
            comment += f"*Next Action:* {progress_data['next_action']}\n"
        
        return comment
    
    def _format_completion_comment(self, result_data: Dict[str, Any]) -> str:
        """Format completion comment."""
        comment = f"*Workflow Completed Successfully* - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if "duration" in result_data:
            comment += f"*Total Duration:* {result_data['duration']}\n"
        
        if "tasks_completed" in result_data:
            comment += f"*Tasks Completed:* {result_data['tasks_completed']}\n"
        
        if "files_modified" in result_data:
            comment += f"*Files Modified:* {result_data['files_modified']}\n"
        
        if "summary" in result_data:
            comment += f"\n*Summary:*\n{result_data['summary']}\n"
        
        return comment
    
    def _format_failure_comment(self, error_data: Dict[str, Any]) -> str:
        """Format failure comment."""
        comment = f"*Workflow Failed* - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if "error_message" in error_data:
            comment += f"*Error:* {error_data['error_message']}\n"
        
        if "failed_task" in error_data:
            comment += f"*Failed Task:* {error_data['failed_task']}\n"
        
        if "recovery_attempted" in error_data:
            comment += f"*Recovery Attempted:* {error_data['recovery_attempted']}\n"
        
        comment += "\n*Manual intervention may be required.*"
        
        return comment
    
    def _get_priority_from_workflow(self, workflow_data: Dict[str, Any]) -> str:
        """Determine JIRA priority from workflow data."""
        priority_map = {
            "low": "Low",
            "medium": "Medium", 
            "high": "High",
            "critical": "Highest"
        }
        
        return priority_map.get(workflow_data.get("priority", "medium"), "Medium")
    
    async def _get_issue_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        """Get available transitions for issue."""
        try:
            response = await self.session.get(f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions")
            if response.status_code == 200:
                return response.json().get("transitions", [])
            return []
        except Exception:
            return []
    
    async def _transition_issue(self, issue_key: str, transition_id: str) -> bool:
        """Transition issue to new status."""
        try:
            transition_data = {
                "transition": {"id": transition_id}
            }
            
            response = await self.session.post(
                f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions",
                json=transition_data
            )
            
            return response.status_code == 204
        except Exception:
            return False
    
    async def _update_custom_fields(self, issue_key: str, progress_data: Dict[str, Any]):
        """Update custom fields with progress data."""
        try:
            # This would be implemented based on specific JIRA custom field configuration
            # Example implementation for common custom fields
            update_data = {"fields": {}}
            
            # Example: Progress percentage custom field
            if "overall_progress" in progress_data:
                # update_data["fields"]["customfield_10001"] = progress_data["overall_progress"]
                pass
            
            if update_data["fields"]:
                await self.session.put(
                    f"{self.base_url}/rest/api/3/issue/{issue_key}",
                    json=update_data
                )
                
        except Exception as e:
            logger.warning(f"Could not update custom fields for {issue_key}: {e}")
    
    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose()