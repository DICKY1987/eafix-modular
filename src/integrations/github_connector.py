"""GitHub integration for repository automation."""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GitHubIssue:
    """GitHub issue representation."""
    number: int
    title: str
    body: str
    state: str
    assignee: Optional[str] = None
    labels: List[str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []

class GitHubConnector:
    """GitHub integration connector."""
    
    def __init__(self, token: str, organization: Optional[str] = None):
        self.token = token
        self.organization = organization
        self.base_url = "https://api.github.com"
        self.session = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
        )
        
    async def test_connection(self) -> Dict[str, Any]:
        """Test GitHub connection."""
        try:
            response = await self.session.get(f"{self.base_url}/user")
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "status": "connected",
                    "user": user_data.get("login"),
                    "name": user_data.get("name")
                }
            else:
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"GitHub connection test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def create_workflow_issue(self, repo: str, workflow_id: str, workflow_data: Dict[str, Any]) -> Optional[GitHubIssue]:
        """Create GitHub issue for workflow execution."""
        try:
            issue_data = {
                "title": f"Workflow Execution: {workflow_data.get('name', workflow_id)}",
                "body": self._format_workflow_description(workflow_id, workflow_data),
                "labels": ["automation", "workflow", f"workflow-{workflow_id}"]
            }
            
            # Add assignee if specified
            assignee = workflow_data.get("assignee")
            if assignee:
                issue_data["assignee"] = assignee
            
            response = await self.session.post(
                f"{self.base_url}/repos/{repo}/issues",
                json=issue_data
            )
            
            if response.status_code == 201:
                result = response.json()
                issue_number = result["number"]
                logger.info(f"Created GitHub issue #{issue_number} for workflow {workflow_id}")
                
                return GitHubIssue(
                    number=issue_number,
                    title=issue_data["title"],
                    body=issue_data["body"],
                    state="open",
                    assignee=assignee,
                    labels=issue_data["labels"]
                )
            else:
                logger.error(f"Failed to create GitHub issue: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating GitHub issue for workflow {workflow_id}: {e}")
            return None
    
    async def add_issue_comment(self, repo: str, issue_number: int, comment: str) -> bool:
        """Add comment to GitHub issue."""
        try:
            comment_data = {"body": comment}
            
            response = await self.session.post(
                f"{self.base_url}/repos/{repo}/issues/{issue_number}/comments",
                json=comment_data
            )
            
            if response.status_code == 201:
                logger.info(f"Added comment to GitHub issue #{issue_number}")
                return True
            else:
                logger.error(f"Failed to add comment: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding comment to issue #{issue_number}: {e}")
            return False
    
    async def update_issue_progress(self, repo: str, issue_number: int, progress_data: Dict[str, Any]) -> bool:
        """Update GitHub issue with workflow progress."""
        try:
            comment = self._format_progress_comment(progress_data)
            return await self.add_issue_comment(repo, issue_number, comment)
                
        except Exception as e:
            logger.error(f"Error updating GitHub issue #{issue_number}: {e}")
            return False
    
    async def close_workflow_issue(self, repo: str, issue_number: int, result_data: Dict[str, Any]) -> bool:
        """Close GitHub issue with results."""
        try:
            # Add completion comment
            comment = self._format_completion_comment(result_data)
            await self.add_issue_comment(repo, issue_number, comment)
            
            # Close the issue
            update_data = {"state": "closed"}
            
            response = await self.session.patch(
                f"{self.base_url}/repos/{repo}/issues/{issue_number}",
                json=update_data
            )
            
            if response.status_code == 200:
                logger.info(f"Closed GitHub issue #{issue_number}")
                return True
            else:
                logger.error(f"Failed to close issue: HTTP {response.status_code}")
                return False
            
        except Exception as e:
            logger.error(f"Error closing GitHub issue #{issue_number}: {e}")
            return False
    
    async def report_workflow_failure(self, repo: str, issue_number: int, error_data: Dict[str, Any]) -> bool:
        """Report workflow failure in GitHub issue."""
        try:
            # Add failure comment
            comment = self._format_failure_comment(error_data)
            await self.add_issue_comment(repo, issue_number, comment)
            
            # Add bug label
            labels_data = {"labels": ["bug", "workflow-failure"]}
            
            response = await self.session.post(
                f"{self.base_url}/repos/{repo}/issues/{issue_number}/labels",
                json=labels_data
            )
            
            logger.info(f"Reported failure for GitHub issue #{issue_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error reporting failure for GitHub issue #{issue_number}: {e}")
            return False
    
    async def create_pull_request(self, repo: str, title: str, body: str, head: str, base: str = "main") -> Optional[Dict[str, Any]]:
        """Create pull request."""
        try:
            pr_data = {
                "title": title,
                "body": body,
                "head": head,
                "base": base
            }
            
            response = await self.session.post(
                f"{self.base_url}/repos/{repo}/pulls",
                json=pr_data
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"Created pull request #{result['number']}")
                return result
            else:
                logger.error(f"Failed to create pull request: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating pull request: {e}")
            return None
    
    async def create_workflow_discussion(self, repo: str, workflow_id: str, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create GitHub discussion for workflow."""
        try:
            # Note: This requires GraphQL API for discussions
            query = """
            mutation CreateDiscussion($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
              createDiscussion(input: {repositoryId: $repositoryId, categoryId: $categoryId, title: $title, body: $body}) {
                discussion {
                  id
                  number
                  url
                }
              }
            }
            """
            
            # For now, fall back to creating an issue
            return await self.create_workflow_issue(repo, workflow_id, workflow_data)
            
        except Exception as e:
            logger.error(f"Error creating GitHub discussion: {e}")
            return None
    
    async def get_repository_info(self, repo: str) -> Optional[Dict[str, Any]]:
        """Get repository information."""
        try:
            response = await self.session.get(f"{self.base_url}/repos/{repo}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting repository info for {repo}: {e}")
            return None
    
    async def list_workflow_runs(self, repo: str, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List GitHub Actions workflow runs."""
        try:
            url = f"{self.base_url}/repos/{repo}/actions/runs"
            params = {}
            
            if workflow_id:
                params["workflow_id"] = workflow_id
            
            response = await self.session.get(url, params=params)
            
            if response.status_code == 200:
                return response.json().get("workflow_runs", [])
            return []
            
        except Exception as e:
            logger.error(f"Error listing workflow runs: {e}")
            return []
    
    async def trigger_workflow_dispatch(self, repo: str, workflow_id: str, ref: str = "main", inputs: Optional[Dict[str, Any]] = None) -> bool:
        """Trigger workflow dispatch event."""
        try:
            dispatch_data = {
                "ref": ref,
                "inputs": inputs or {}
            }
            
            response = await self.session.post(
                f"{self.base_url}/repos/{repo}/actions/workflows/{workflow_id}/dispatches",
                json=dispatch_data
            )
            
            if response.status_code == 204:
                logger.info(f"Triggered workflow {workflow_id} in {repo}")
                return True
            else:
                logger.error(f"Failed to trigger workflow: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error triggering workflow dispatch: {e}")
            return False
    
    def _format_workflow_description(self, workflow_id: str, workflow_data: Dict[str, Any]) -> str:
        """Format workflow description for GitHub."""
        description = f"## Automated Workflow Execution\n\n"
        description += f"**Workflow ID:** `{workflow_id}`\n"
        description += f"**Started:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if "description" in workflow_data:
            description += f"**Description:** {workflow_data['description']}\n\n"
        
        if "tasks" in workflow_data:
            description += f"**Tasks:** {len(workflow_data['tasks'])}\n"
        
        if "estimated_duration" in workflow_data:
            description += f"**Estimated Duration:** {workflow_data['estimated_duration']}\n\n"
        
        description += "Progress will be updated automatically as the workflow executes.\n\n"
        description += "---\n*This issue was created automatically by the workflow orchestration system.*"
        
        return description
    
    def _format_progress_comment(self, progress_data: Dict[str, Any]) -> str:
        """Format progress update comment."""
        comment = f"## Workflow Progress Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if "overall_progress" in progress_data:
            progress = progress_data["overall_progress"]
            progress_bar = self._create_progress_bar(progress)
            comment += f"**Overall Progress:** {progress_bar} {progress}%\n\n"
        
        if "current_phase" in progress_data:
            comment += f"**Current Phase:** {progress_data['current_phase']}\n"
        
        if "completed_tasks" in progress_data:
            comment += f"**Completed Tasks:** {progress_data['completed_tasks']}\n"
        
        if "remaining_tasks" in progress_data:
            comment += f"**Remaining Tasks:** {progress_data['remaining_tasks']}\n"
        
        if "next_action" in progress_data:
            comment += f"**Next Action:** {progress_data['next_action']}\n"
        
        return comment
    
    def _format_completion_comment(self, result_data: Dict[str, Any]) -> str:
        """Format completion comment."""
        comment = f"## ✅ Workflow Completed Successfully - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if "duration" in result_data:
            comment += f"**Total Duration:** {result_data['duration']}\n"
        
        if "tasks_completed" in result_data:
            comment += f"**Tasks Completed:** {result_data['tasks_completed']}\n"
        
        if "files_modified" in result_data:
            comment += f"**Files Modified:** {result_data['files_modified']}\n\n"
        
        if "summary" in result_data:
            comment += f"**Summary:**\n{result_data['summary']}\n\n"
        
        comment += "---\n*Workflow execution completed successfully. This issue will now be closed.*"
        
        return comment
    
    def _format_failure_comment(self, error_data: Dict[str, Any]) -> str:
        """Format failure comment."""
        comment = f"## ❌ Workflow Failed - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if "error_message" in error_data:
            comment += f"**Error:**\n```\n{error_data['error_message']}\n```\n\n"
        
        if "failed_task" in error_data:
            comment += f"**Failed Task:** {error_data['failed_task']}\n"
        
        if "recovery_attempted" in error_data:
            recovery_status = "Yes" if error_data['recovery_attempted'] else "No"
            comment += f"**Recovery Attempted:** {recovery_status}\n\n"
        
        comment += "**Action Required:** Manual intervention may be needed to resolve this issue.\n\n"
        comment += "---\n*This issue has been labeled as a workflow failure for investigation.*"
        
        return comment
    
    def _create_progress_bar(self, percent: int, length: int = 20) -> str:
        """Create ASCII progress bar."""
        filled_length = int(length * percent // 100)
        bar = '█' * filled_length + '░' * (length - filled_length)
        return f"[{bar}]"
    
    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose()