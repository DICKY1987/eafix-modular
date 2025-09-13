"""
Git Integration for LangGraph Multi-Agent System
Replaces your complex PowerShell git worktree management
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import json

from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

@dataclass
class LaneConfig:
    name: str
    branch: str
    worktree_path: str
    allowed_patterns: List[str]
    tools: Dict[str, str]
    agent_type: str

class GitLaneManager:
    """Replaces your entire PowerShell git worktree system"""
    
    def __init__(self, config_path: str = ".ai/framework-config.json"):
        self.config = self.load_config(config_path)
        self.lanes = self.setup_lanes()

    def load_config(self, config_path: str) -> Dict:
        """Load your existing framework configuration"""
        config_file = Path(config_path)
        if config_file.exists():
            return json.loads(config_file.read_text())
        return self.get_default_config()

    def get_default_config(self) -> Dict:
        """Your exact lane configuration from the PowerShell script"""
        return {
            "lanes": {
                "ai_coding": {
                    "name": "AI Code Generation",
                    "worktreePath": ".worktrees/ai-coding",
                    "branch": "lane/ai-coding", 
                    "allowedPatterns": ["src/**", "lib/**", "tests/**"],
                    "tools": {"primary": {"tool": "aider"}},
                    "agent_type": "aider_local"
                },
                "agentic_architecture": {
                    "name": "System Architecture & Complex Design",
                    "worktreePath": ".worktrees/architecture",
                    "branch": "lane/architecture",
                    "allowedPatterns": ["architecture/**", "design/**", "*.arch.md"],
                    "tools": {"primary": {"tool": "claude_code"}},
                    "agent_type": "claude_code"
                },
                "quality": {
                    "name": "Code Quality",
                    "worktreePath": ".worktrees/quality", 
                    "branch": "lane/quality",
                    "allowedPatterns": ["**/*.js", "**/*.py", "**/*.sql"],
                    "tools": {"linting": {"python": "ruff check --fix ."}},
                    "agent_type": "gemini_cli"
                }
            }
        }

    def setup_lanes(self) -> Dict[str, LaneConfig]:
        """Initialize git worktrees (replaces PowerShell Initialize-Lanes)"""
        lanes = {}
        
        for lane_name, lane_data in self.config["lanes"].items():
            lane = LaneConfig(
                name=lane_data["name"],
                branch=lane_data["branch"], 
                worktree_path=lane_data["worktreePath"],
                allowed_patterns=lane_data.get("allowedPatterns", ["**/*"]),
                tools=lane_data.get("tools", {}),
                agent_type=lane_data.get("agent_type", "gemini_cli")
            )
            
            # Create worktree if it doesn't exist
            self.create_worktree(lane)
            lanes[lane_name] = lane
            
        return lanes

    def create_worktree(self, lane: LaneConfig) -> bool:
        """Create git worktree (replaces PowerShell worktree creation)"""
        try:
            worktree_path = Path(lane.worktree_path)
            
            if worktree_path.exists():
                print(f"OK Worktree already exists: {lane.name}")
                return True
                
            # Create parent directory
            worktree_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if branch exists
            branch_exists = subprocess.run(
                ["git", "rev-parse", "--verify", lane.branch],
                capture_output=True, text=True
            ).returncode == 0
            
            if branch_exists:
                # Add existing branch
                subprocess.run([
                    "git", "worktree", "add", str(worktree_path), lane.branch
                ], check=True)
            else:
                # Create new branch from main
                subprocess.run([
                    "git", "worktree", "add", str(worktree_path), "-b", lane.branch, "main"
                ], check=True)
            
            print(f"OK Created worktree: {lane.name} -> {worktree_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"ERROR Failed to create worktree {lane.name}: {e}")
            return False

    def get_lane_status(self) -> Dict[str, Dict[str, str]]:
        """Get status of all lanes (replaces PowerShell lane status)"""
        status = {}
        
        for lane_name, lane in self.lanes.items():
            worktree_path = Path(lane.worktree_path)
            
            if not worktree_path.exists():
                status[lane_name] = {"status": "Not initialized", "branch": "N/A"}
                continue
                
            try:
                # Get current branch
                branch_result = subprocess.run(
                    ["git", "-C", str(worktree_path), "branch", "--show-current"],
                    capture_output=True, text=True, check=True
                )
                current_branch = branch_result.stdout.strip()
                
                # Get working directory status
                status_result = subprocess.run(
                    ["git", "-C", str(worktree_path), "status", "--porcelain"],
                    capture_output=True, text=True, check=True
                )
                has_changes = len(status_result.stdout.strip()) > 0
                
                status[lane_name] = {
                    "status": "Ready" if not has_changes else "Modified",
                    "branch": current_branch,
                    "changes": "Yes" if has_changes else "No"
                }
                
            except subprocess.CalledProcessError:
                status[lane_name] = {"status": "Error", "branch": "Unknown"}
                
        return status

# Git-aware tools for LangGraph agents
@tool
def check_file_patterns(file_path: str, allowed_patterns: List[str]) -> bool:
    """Check if file matches lane's allowed patterns"""
    from fnmatch import fnmatch
    
    for pattern in allowed_patterns:
        if fnmatch(file_path, pattern):
            return True
    return False

@tool
def commit_changes(lane_name: str, message: str, git_manager: GitLaneManager) -> Dict[str, str]:
    """Commit changes in a specific lane"""
    if lane_name not in git_manager.lanes:
        return {"error": f"Lane {lane_name} not found"}
    
    lane = git_manager.lanes[lane_name]
    worktree_path = Path(lane.worktree_path)
    
    try:
        # Add files
        subprocess.run(
            ["git", "-C", str(worktree_path), "add", "."],
            check=True
        )
        
        # Commit with lane prefix (like your PowerShell commitPrefix)
        commit_msg = f"{lane_name}: {message}"
        subprocess.run(
            ["git", "-C", str(worktree_path), "commit", "-m", commit_msg],
            check=True
        )
        
        return {"success": f"Committed changes in {lane_name}"}
        
    except subprocess.CalledProcessError as e:
        return {"error": f"Failed to commit: {e}"}

class LaneAwareAgent:
    """LangGraph agent that understands git lanes"""
    
    def __init__(self, lane_config: LaneConfig, git_manager: GitLaneManager):
        self.lane = lane_config
        self.git_manager = git_manager
        
        # Create agent with lane-specific tools
        tools = [
            lambda fp: check_file_patterns(fp, self.lane.allowed_patterns),
            lambda msg: commit_changes(self.lane.name, msg, self.git_manager)
        ]
        
        # Select model based on lane's agent type
        if self.lane.agent_type == "claude_code":
            from langchain_anthropic import ChatAnthropic
            model = ChatAnthropic(model="claude-3-sonnet-20240229")
        elif self.lane.agent_type == "gemini_cli":
            from langchain_google_genai import ChatGoogleGenerativeAI  
            model = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
        else:  # aider_local/ollama
            from langchain_community.llms import Ollama
            model = Ollama(model="codellama:7b-instruct")
        
        self.agent = create_react_agent(
            model, 
            tools,
            state_modifier=f"You are working in the {self.lane.name} lane. Only modify files matching these patterns: {self.lane.allowed_patterns}"
        )

def create_multi_lane_graph(git_manager: GitLaneManager) -> StateGraph:
    """Create a multi-lane workflow graph"""
    
    class LaneState(MessagesState):
        selected_lane: str = ""
        target_files: List[str] = []
    
    def select_lane(state: LaneState) -> LaneState:
        """Select appropriate lane based on task and file patterns"""
        messages = state["messages"]
        task = messages[-1].content if messages else ""
        
        # Simple lane selection logic (enhance as needed)
        if "architecture" in task.lower() or "design" in task.lower():
            return {"selected_lane": "agentic_architecture"}
        elif "quality" in task.lower() or "lint" in task.lower():
            return {"selected_lane": "quality"}
        else:
            return {"selected_lane": "ai_coding"}
    
    def route_to_lane(state: LaneState) -> str:
        return state["selected_lane"]
    
    # Build workflow
    workflow = StateGraph(LaneState)
    workflow.add_node("select_lane", select_lane)
    
    # Add lane-specific agents
    for lane_name, lane_config in git_manager.lanes.items():
        agent = LaneAwareAgent(lane_config, git_manager)
        workflow.add_node(lane_name, agent.agent)
    
    # Add routing
    workflow.add_edge("START", "select_lane")
    workflow.add_conditional_edges("select_lane", route_to_lane)
    
    for lane_name in git_manager.lanes.keys():
        workflow.add_edge(lane_name, "END")
    
    return workflow.compile()

# CLI commands for git integration
def add_git_commands(cli_group):
    """Add git-related commands to your CLI"""
    
    @cli_group.command()
    def init_lanes():
        """Initialize all git worktree lanes"""
        git_manager = GitLaneManager()
        print("Lanes initialized successfully!")
    
    @cli_group.command()
    def lane_status():
        """Show status of all lanes"""
        git_manager = GitLaneManager()
        status = git_manager.get_lane_status()
        
        print("\nLane Status:")
        for lane_name, info in status.items():
            print(f"  {lane_name}: {info['status']} (Branch: {info['branch']})")
    
    @cli_group.command()
    @click.argument('lane_name')
    def open_lane(lane_name: str):
        """Open a lane in VS Code (replaces PowerShell Start-Lane)"""
        git_manager = GitLaneManager()
        
        if lane_name not in git_manager.lanes:
            print(f"ERROR Lane '{lane_name}' not found")
            return
            
        lane = git_manager.lanes[lane_name]
        worktree_path = Path(lane.worktree_path)
        
        if worktree_path.exists():
            vscode_cmd = f'code "{worktree_path}"'
            print(f"💻 Opening {lane.name} in VS Code:")
            print(f"   {vscode_cmd}")
            subprocess.run(["code", str(worktree_path)])
        else:
            print(f"ERROR Worktree not found: {worktree_path}")
