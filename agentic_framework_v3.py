#!/usr/bin/env python3
"""
Modern Multi-Agent Development Framework v3.0
Cost-Optimized Development Orchestration with Framework Integration

Core Innovation: Cost-first AI development with intelligent service routing
Built on: CrewAI + LangGraph + Hydra + Redis + FastAPI
"""

import asyncio
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Literal, Any
from dataclasses import dataclass
import json

# Core Framework Imports
from crewai import Agent, Task, Crew
from langgraph.graph import StateGraph, MessagesState, START, END
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField, create_engine, Session, select
import redis.asyncio as redis
from datetime import timedelta
from fastapi import FastAPI, BackgroundTasks
import typer
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from prometheus_client import Counter, Histogram, Gauge
import structlog

# Import git integration
try:
    from langgraph_git_integration import GitLaneManager, LaneConfig
except ImportError:
    # Fallback if git integration is not available
    class GitLaneManager:
        def __init__(self, config_path=None):
            self.lanes = {}
        def get_lane_for_task(self, task_description):
            return None
    class LaneConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
import httpx
import subprocess
import os
from urllib.parse import urljoin
from pathlib import Path
from fnmatch import fnmatch

# Initialize rich console and logging
console = Console()
logger = structlog.get_logger()

# Metrics
SERVICE_REQUESTS = Counter('service_requests_total', 'Service requests', ['service'])
TASK_DURATION = Histogram('task_duration_seconds', 'Task execution time')
DAILY_COST = Gauge('daily_cost_dollars', 'Daily cost accumulation')

class TaskComplexity(str, Enum):
    """Task complexity classification"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"

class ServiceType(str, Enum):
    """Available AI services"""
    GEMINI_CLI = "gemini_cli"
    CLAUDE_CODE = "claude_code"
    AIDER_LOCAL = "aider_local"
    OLLAMA_LOCAL = "ollama_local"

class ExecutionStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    QUOTA_EXCEEDED = "quota_exceeded"

@dataclass
class ServiceConfig:
    """Service configuration with cost and quota management"""
    daily_limit: int
    cost_per_request: float
    priority: int
    complexity_match: List[str]
    fallback: Optional[str] = None

# Service Configuration - Core Innovation Layer
SERVICES = {
    ServiceType.GEMINI_CLI: ServiceConfig(
        daily_limit=1000,
        cost_per_request=0.0,
        priority=1,
        complexity_match=["simple", "moderate"],
        fallback="ollama_local"
    ),
    ServiceType.CLAUDE_CODE: ServiceConfig(
        daily_limit=25,
        cost_per_request=0.15,
        priority=2,
        complexity_match=["complex", "moderate"],
        fallback="aider_local"
    ),
    ServiceType.AIDER_LOCAL: ServiceConfig(
        daily_limit=999999,
        cost_per_request=0.0,
        priority=3,
        complexity_match=["moderate", "complex"],
        fallback="ollama_local"
    ),
    ServiceType.OLLAMA_LOCAL: ServiceConfig(
        daily_limit=999999,
        cost_per_request=0.0,
        priority=4,
        complexity_match=["simple", "moderate", "complex"]
    )
}

# Data Models with SQLModel
class WorkflowExecution(SQLModel, table=True):
    """Persistent workflow execution tracking"""
    id: Optional[int] = SQLField(default=None, primary_key=True)
    workflow_id: str
    task_description: str
    complexity: TaskComplexity
    selected_service: ServiceType
    status: ExecutionStatus
    cost_estimate: float
    actual_cost: float = 0.0
    start_time: datetime = SQLField(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    service_usage: str = SQLField(default="{}")  # JSON string instead of dict
    results: Optional[str] = None  # JSON string instead of dict
    selected_lane: Optional[str] = None
    worktree_path: Optional[str] = None
    committed: bool = False
    commit_message: Optional[str] = None

class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self, database_url: str = "sqlite:///./workflow_executions.db"):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        # Create tables
        SQLModel.metadata.create_all(self.engine)
    
    def create_execution(self, 
                        task_description: str, 
                        complexity: TaskComplexity,
                        selected_service: ServiceType,
                        workflow_id: Optional[str] = None) -> WorkflowExecution:
        """Create a new workflow execution record"""
        
        if workflow_id is None:
            import uuid
            workflow_id = str(uuid.uuid4())
        
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            task_description=task_description,
            complexity=complexity,
            selected_service=selected_service,
            status=ExecutionStatus.PENDING,
            cost_estimate=SERVICES[selected_service].cost_per_request
        )
        
        with Session(self.engine) as session:
            session.add(execution)
            session.commit()
            session.refresh(execution)
        
        return execution
    
    def update_execution_status(self, execution_id: int, status: ExecutionStatus) -> bool:
        """Update execution status"""
        with Session(self.engine) as session:
            statement = select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
            execution = session.exec(statement).first()
            
            if execution:
                execution.status = status
                if status == ExecutionStatus.COMPLETED:
                    execution.end_time = datetime.utcnow()
                session.add(execution)
                session.commit()
                return True
            return False
    
    def update_execution_results(self, execution_id: int, results: Dict[str, Any]) -> bool:
        """Update execution results"""
        import json
        
        with Session(self.engine) as session:
            statement = select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
            execution = session.exec(statement).first()
            
            if execution:
                execution.results = json.dumps(results)
                execution.actual_cost = results.get('total_cost', execution.cost_estimate)
                
                # Update git-related fields if present
                if 'lane_used' in results:
                    execution.selected_lane = results['lane_used']
                if 'worktree_path' in results:
                    execution.worktree_path = results['worktree_path']
                if 'committed' in results:
                    execution.committed = results['committed']
                if 'commit_message' in results:
                    execution.commit_message = results['commit_message']
                
                session.add(execution)
                session.commit()
                return True
            return False
    
    def get_daily_stats(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get daily execution statistics"""
        if date is None:
            date = datetime.utcnow()
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        with Session(self.engine) as session:
            statement = (select(WorkflowExecution)
                        .where(WorkflowExecution.start_time >= start_of_day)
                        .where(WorkflowExecution.start_time <= end_of_day))
            executions = list(session.exec(statement))
        
        stats = {
            "date": date.strftime("%Y-%m-%d"),
            "total_executions": len(executions),
            "by_service": {},
            "by_status": {},
            "by_complexity": {},
            "total_cost": 0.0,
            "average_duration": 0.0
        }
        
        durations = []
        
        for execution in executions:
            # By service
            service = execution.selected_service.value
            stats["by_service"][service] = stats["by_service"].get(service, 0) + 1
            
            # By status
            status = execution.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # By complexity
            complexity = execution.complexity.value
            stats["by_complexity"][complexity] = stats["by_complexity"].get(complexity, 0) + 1
            
            # Cost
            stats["total_cost"] += execution.actual_cost
            
            # Duration
            if execution.end_time:
                duration = (execution.end_time - execution.start_time).total_seconds()
                durations.append(duration)
        
        if durations:
            stats["average_duration"] = sum(durations) / len(durations)
        
        return stats

class TaskRequest(BaseModel):
    """API request model for tasks"""
    description: str
    complexity: Optional[TaskComplexity] = None
    max_cost: Optional[float] = None
    force_agent: Optional[ServiceType] = None
    lane: Optional[str] = None

class DevWorkflowState(BaseModel):
    """LangGraph state for development workflows"""
    task_description: str
    complexity: TaskComplexity = TaskComplexity.SIMPLE
    selected_service: ServiceType = ServiceType.GEMINI_CLI
    cost_estimate: float = 0.0
    quota_approved: bool = False
    worktree_path: Optional[str] = None
    selected_lane: Optional[str] = None
    lane_config: Optional[Dict[str, Any]] = None
    target_files: List[str] = Field(default_factory=list)
    results: Dict[str, Any] = Field(default_factory=dict)
    execution_id: Optional[int] = None

class CostOptimizedQuotaManager:
    """Redis-based quota management with cost optimization"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = None
        self.redis_url = redis_url
    
    async def connect(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(self.redis_url)
    
    async def get_daily_usage(self, service: ServiceType) -> int:
        """Get current daily usage for a service"""
        today = datetime.now().strftime("%Y-%m-%d")
        usage = await self.redis_client.hget(f"daily_usage:{today}", service.value)
        return int(usage) if usage else 0
    
    async def update_usage(self, service: ServiceType, count: int = 1):
        """Update service usage with atomic operations"""
        today = datetime.now().strftime("%Y-%m-%d")
        await self.redis_client.hincrby(f"daily_usage:{today}", service.value, count)
        await self.redis_client.expire(f"daily_usage:{today}", 86400)  # 24 hours
        
        # Update metrics
        SERVICE_REQUESTS.labels(service=service.value).inc(count)
        cost = count * SERVICES[service].cost_per_request
        DAILY_COST.inc(cost)
        
        logger.info("quota_updated", service=service.value, count=count, cost=cost)
    
    async def check_quota_available(self, service: ServiceType) -> bool:
        """Check if quota is available for service"""
        usage = await self.get_daily_usage(service)
        limit = SERVICES[service].daily_limit
        return usage < limit
    
    async def get_cost_warning_level(self, service: ServiceType) -> float:
        """Get warning level for cost-conscious services"""
        if SERVICES[service].cost_per_request == 0:
            return 0.0
        
        usage = await self.get_daily_usage(service)
        limit = SERVICES[service].daily_limit
        return usage / limit if limit > 0 else 0.0

class TaskComplexityAnalyzer:
    """AI-powered task complexity classification"""
    
    COMPLEX_KEYWORDS = [
        "architecture", "redesign", "refactor large", "performance", 
        "security audit", "database migration", "infrastructure",
        "system design", "scalability", "distributed", "microservices"
    ]
    
    MODERATE_KEYWORDS = [
        "feature", "implement", "add component", "API", "integration",
        "module", "service", "endpoint", "function", "class"
    ]
    
    def classify_complexity(self, task_description: str) -> TaskComplexity:
        """Classify task complexity based on description"""
        task_lower = task_description.lower()
        
        if any(keyword in task_lower for keyword in self.COMPLEX_KEYWORDS):
            return TaskComplexity.COMPLEX
        elif any(keyword in task_lower for keyword in self.MODERATE_KEYWORDS):
            return TaskComplexity.MODERATE
        
        return TaskComplexity.SIMPLE

class CostOptimizedServiceRouter:
    """Core innovation: Cost-aware service routing with git integration"""
    
    def __init__(self, quota_manager: CostOptimizedQuotaManager, git_manager: Optional[GitLaneManager] = None):
        self.quota_manager = quota_manager
        self.analyzer = TaskComplexityAnalyzer()
        self.git_manager = git_manager or GitLaneManager()
    
    def select_lane_for_task(self, task_description: str) -> Optional[str]:
        """Select appropriate git lane based on task content"""
        task_lower = task_description.lower()
        
        # Architecture/design tasks
        if any(keyword in task_lower for keyword in 
               ['architecture', 'design', 'system design', 'scalability', 'microservices']):
            return 'agentic_architecture'
        
        # Quality/linting tasks
        elif any(keyword in task_lower for keyword in 
                ['quality', 'lint', 'format', 'style', 'refactor']):
            return 'quality'
        
        # Default to coding lane
        else:
            return 'ai_coding'
    
    def get_service_for_lane(self, lane_name: str) -> ServiceType:
        """Get the preferred service for a specific lane"""
        if not self.git_manager or lane_name not in self.git_manager.lanes:
            return ServiceType.GEMINI_CLI
        
        lane_config = self.git_manager.lanes[lane_name]
        agent_type = getattr(lane_config, 'agent_type', 'gemini_cli')
        
        # Map agent type to service type
        service_map = {
            'claude_code': ServiceType.CLAUDE_CODE,
            'aider_local': ServiceType.AIDER_LOCAL,
            'gemini_cli': ServiceType.GEMINI_CLI,
            'ollama_local': ServiceType.OLLAMA_LOCAL
        }
        
        return service_map.get(agent_type, ServiceType.GEMINI_CLI)
    
    async def select_optimal_service(
        self, 
        task_description: str,
        complexity: Optional[TaskComplexity] = None,
        max_cost: Optional[float] = None,
        lane: Optional[str] = None
    ) -> tuple[ServiceType, Optional[str]]:
        """Select optimal service based on complexity, cost, availability, and git lane"""
        
        # Select lane if not provided
        if lane is None:
            lane = self.select_lane_for_task(task_description)
        
        # Get lane-preferred service if available
        lane_preferred_service = None
        if lane and self.git_manager and lane in self.git_manager.lanes:
            lane_preferred_service = self.get_service_for_lane(lane)
        
        # Determine complexity if not provided
        if complexity is None:
            complexity = self.analyzer.classify_complexity(task_description)
        
        # Get services that can handle this complexity
        candidate_services = [
            service for service, config in SERVICES.items()
            if complexity.value in config.complexity_match
        ]
        
        # Prioritize lane-preferred service if it can handle the complexity
        if (lane_preferred_service and 
            lane_preferred_service in candidate_services):
            # Move preferred service to front
            candidate_services.remove(lane_preferred_service)
            candidate_services.insert(0, lane_preferred_service)
        
        # Sort by priority (lower = higher priority)
        candidate_services.sort(key=lambda s: SERVICES[s].priority)
        
        # Check each service in priority order
        for service in candidate_services:
            config = SERVICES[service]
            
            # Check quota availability
            if not await self.quota_manager.check_quota_available(service):
                console.print(f"⚠️  {service.value} quota exceeded, trying next option...")
                continue
            
            # Check cost constraints
            if max_cost and config.cost_per_request > max_cost:
                console.print(f"💰 {service.value} cost ${config.cost_per_request} exceeds limit ${max_cost}")
                continue
            
            # Special handling for premium services
            if config.cost_per_request > 0:
                warning_level = await self.quota_manager.get_cost_warning_level(service)
                if warning_level > 0.6:  # 60% of quota used
                    current_usage = await self.quota_manager.get_daily_usage(service)
                    total_cost = current_usage * config.cost_per_request
                    
                    console.print(f"⚠️  {service.value} usage: {current_usage}/{config.daily_limit}")
                    console.print(f"💰 Cost today: ${total_cost:.2f}")
                    
                    if not typer.confirm(f"Continue with {service.value}?"):
                        continue
            
            lane_info = f" in {lane} lane" if lane else ""
            console.print(f"🎯 Selected: {service.value} for {complexity.value} task{lane_info}")
            return service, lane
        
        # Fallback to unlimited local service
        console.print("⚠️  All preferred services unavailable, using local fallback")
        return ServiceType.OLLAMA_LOCAL, lane

class AIServiceClient:
    """Base class for AI service clients"""
    
    def __init__(self, service_type: ServiceType):
        self.service_type = service_type
        self.config = SERVICES[service_type]
    
    async def execute_task(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a task using this service"""
        raise NotImplementedError
    
    async def is_available(self) -> bool:
        """Check if service is available"""
        return True

class GeminiClient(AIServiceClient):
    """Google Gemini API client"""
    
    def __init__(self):
        super().__init__(ServiceType.GEMINI_CLI)
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
        
    async def execute_task(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute task using Gemini API"""
        if not self.api_key:
            return {"error": "GOOGLE_API_KEY not configured"}
            
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"Task: {task_description}\n\nProvide a detailed solution with implementation steps."
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}?key={self.api_key}",
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                
                if "candidates" in result and result["candidates"]:
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    return {
                        "success": True,
                        "service": "gemini",
                        "result": content,
                        "usage": result.get("usageMetadata", {})
                    }
                else:
                    return {"error": "No response from Gemini API"}
                    
        except Exception as e:
            logger.error("gemini_api_error", error=str(e))
            return {"error": f"Gemini API error: {str(e)}"}
    
    async def is_available(self) -> bool:
        """Check if Gemini API is available"""
        return bool(self.api_key)

class ClaudeClient(AIServiceClient):
    """Anthropic Claude API client"""
    
    def __init__(self):
        super().__init__(ServiceType.CLAUDE_CODE)
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1/messages"
    
    async def execute_task(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute task using Claude API"""
        if not self.api_key:
            return {"error": "ANTHROPIC_API_KEY not configured"}
            
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 2048,
            "messages": [{
                "role": "user",
                "content": f"Task: {task_description}\n\nAs an expert software architect, provide a comprehensive solution with detailed implementation steps, code examples, and best practices."
            }]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
                
                if "content" in result and result["content"]:
                    content = result["content"][0]["text"]
                    return {
                        "success": True,
                        "service": "claude",
                        "result": content,
                        "usage": result.get("usage", {})
                    }
                else:
                    return {"error": "No response from Claude API"}
                    
        except Exception as e:
            logger.error("claude_api_error", error=str(e))
            return {"error": f"Claude API error: {str(e)}"}
    
    async def is_available(self) -> bool:
        """Check if Claude API is available"""
        return bool(self.api_key)

class AiderClient(AIServiceClient):
    """Aider local client"""
    
    def __init__(self):
        super().__init__(ServiceType.AIDER_LOCAL)
        self.aider_path = "aider"  # Assume aider is in PATH
    
    async def execute_task(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute task using Aider"""
        try:
            # Check if aider is available
            subprocess.run([self.aider_path, "--version"], 
                          capture_output=True, check=True, timeout=10)
            
            # Create a temporary file with the task description
            task_file = "aider_task.md"
            with open(task_file, "w") as f:
                f.write(f"# Task\n\n{task_description}\n\n")
                f.write("Please implement this task with proper code and documentation.")
            
            # Run aider with the task
            cmd = [self.aider_path, "--yes", "--message", task_description, task_file]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "service": "aider",
                    "result": stdout.decode(),
                    "files_modified": [task_file]
                }
            else:
                return {"error": f"Aider failed: {stderr.decode()}"}
                
        except subprocess.CalledProcessError:
            return {"error": "Aider not found or not working"}
        except asyncio.TimeoutError:
            return {"error": "Aider execution timed out"}
        except Exception as e:
            logger.error("aider_error", error=str(e))
            return {"error": f"Aider error: {str(e)}"}
    
    async def is_available(self) -> bool:
        """Check if Aider is available"""
        try:
            subprocess.run([self.aider_path, "--version"], 
                          capture_output=True, check=True, timeout=5)
            return True
        except:
            return False

class OllamaClient(AIServiceClient):
    """Ollama local client"""
    
    def __init__(self):
        super().__init__(ServiceType.OLLAMA_LOCAL)
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = "codellama:7b"  # Default model
    
    async def execute_task(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute task using Ollama"""
        try:
            payload = {
                "model": self.model,
                "prompt": f"Task: {task_description}\n\nProvide a detailed implementation with code examples and explanations.",
                "stream": False
            }
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                return {
                    "success": True,
                    "service": "ollama",
                    "result": result.get("response", ""),
                    "model": self.model
                }
                
        except Exception as e:
            logger.error("ollama_error", error=str(e))
            return {"error": f"Ollama error: {str(e)}"}
    
    async def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False

class DevAgentCrew:
    """CrewAI-based multi-agent system with real AI service clients"""
    
    def __init__(self):
        # Initialize AI service clients
        self.clients = {
            ServiceType.GEMINI_CLI: GeminiClient(),
            ServiceType.CLAUDE_CODE: ClaudeClient(),
            ServiceType.AIDER_LOCAL: AiderClient(),
            ServiceType.OLLAMA_LOCAL: OllamaClient()
        }
        self.agents = self._create_agents()
    
    def _create_agents(self) -> Dict[str, Agent]:
        """Create specialized development agents"""
        
        researcher = Agent(
            role='Research Specialist',
            goal='Gather information using cost-effective services',
            backstory='Optimized for free-tier services and efficient research',
            tools=[],  # Tools will be assigned dynamically
            verbose=True
        )
        
        architect = Agent(
            role='System Architect',
            goal='Design solutions for complex problems',
            backstory='Uses premium services only when complexity justifies cost',
            tools=[],  # Tools will be assigned dynamically
            verbose=True
        )
        
        implementer = Agent(
            role='Code Implementer',
            goal='Generate code using local and free services',
            backstory='Specialist in local tools and cost-free implementation',
            tools=[],  # Tools will be assigned dynamically
            verbose=True
        )
        
        return {
            'researcher': researcher,
            'architect': architect,
            'implementer': implementer
        }
    
    async def get_service_client(self, service_type: ServiceType) -> AIServiceClient:
        """Get the appropriate service client"""
        return self.clients[service_type]
    
    def create_task(self, description: str, agent_role: str) -> Task:
        """Create a task for specific agent"""
        return Task(
            description=description,
            agent=self.agents[agent_role],
            expected_output="Completed task with detailed results"
        )
    
    async def execute_research_plan_code_workflow(
        self, 
        task_description: str,
        selected_service: ServiceType
    ) -> Dict[str, Any]:
        """Execute the research-plan-code workflow using real AI services"""
        
        workflow_results = []
        total_cost = 0.0
        
        try:
            # Phase 1: Research (use free service - Gemini or Ollama)
            research_service = ServiceType.GEMINI_CLI
            client = await self.get_service_client(research_service)
            
            if not await client.is_available():
                research_service = ServiceType.OLLAMA_LOCAL
                client = await self.get_service_client(research_service)
            
            console.print(f"🔍 Research phase using {research_service.value}")
            research_result = await client.execute_task(
                f"Research and analyze requirements for: {task_description}. Provide context, best practices, and approach recommendations."
            )
            workflow_results.append({
                "phase": "research",
                "service": research_service.value,
                "result": research_result
            })
            
            # Phase 2: Planning (use selected service for complex tasks)
            if selected_service in [ServiceType.CLAUDE_CODE, ServiceType.AIDER_LOCAL]:
                console.print(f"📋 Planning phase using {selected_service.value}")
                planning_client = await self.get_service_client(selected_service)
                
                context = research_result.get('result', '') if research_result.get('success') else ''
                planning_prompt = f"""Based on this research: {context[:1000]}...
                
Create a detailed implementation plan for: {task_description}
                Include:
                - Architecture decisions
                - Step-by-step implementation
                - Code structure
                - Dependencies and tools needed
                """
                
                planning_result = await planning_client.execute_task(planning_prompt)
                workflow_results.append({
                    "phase": "planning",
                    "service": selected_service.value,
                    "result": planning_result
                })
                
                total_cost += SERVICES[selected_service].cost_per_request
            
            # Phase 3: Implementation (use the selected service)
            console.print(f"⚡ Implementation phase using {selected_service.value}")
            implementation_client = await self.get_service_client(selected_service)
            
            # Gather context from previous phases
            context_parts = []
            for phase_result in workflow_results:
                if phase_result['result'].get('success'):
                    context_parts.append(f"{phase_result['phase'].title()}: {phase_result['result']['result'][:500]}")
            
            context = "\n\n".join(context_parts)
            implementation_prompt = f"""Context from previous phases:
{context}

Now implement: {task_description}

Provide:
- Complete working code
- Documentation
- Usage examples
- Error handling
"""
            
            implementation_result = await implementation_client.execute_task(implementation_prompt)
            workflow_results.append({
                "phase": "implementation",
                "service": selected_service.value,
                "result": implementation_result
            })
            
            total_cost += SERVICES[selected_service].cost_per_request
            
            # Compile final result
            final_result = {
                "workflow_type": "research_plan_code",
                "service_used": selected_service.value,
                "phases_completed": len(workflow_results),
                "total_cost": total_cost,
                "workflow_results": workflow_results,
                "success": True
            }
            
            # Extract the main implementation result
            if implementation_result.get('success'):
                final_result['result'] = implementation_result['result']
            else:
                final_result['result'] = "Implementation completed with some issues. Check workflow_results for details."
            
            return final_result
            
        except Exception as e:
            logger.error("workflow_execution_error", error=str(e))
            return {
                "workflow_type": "research_plan_code",
                "service_used": selected_service.value,
                "error": str(e),
                "partial_results": workflow_results,
                "total_cost": total_cost,
                "success": False
            }

class LangGraphWorkflowEngine:
    """LangGraph-based workflow orchestration with git integration"""
    
    def __init__(self, service_router: CostOptimizedServiceRouter, agent_crew: DevAgentCrew, git_manager: Optional[GitLaneManager] = None):
        self.service_router = service_router
        self.agent_crew = agent_crew
        self.git_manager = git_manager
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the main development workflow"""
        
        workflow = StateGraph(DevWorkflowState)
        
        # Add workflow nodes
        workflow.add_node("analyze_task", self._analyze_task)
        workflow.add_node("select_lane", self._select_lane)
        workflow.add_node("route_service", self._route_service)
        workflow.add_node("setup_worktree", self._setup_worktree)
        workflow.add_node("cost_approval", self._cost_approval)
        workflow.add_node("execute_task", self._execute_task)
        workflow.add_node("commit_changes", self._commit_changes)
        workflow.add_node("update_metrics", self._update_metrics)
        
        # Define workflow edges
        workflow.add_edge(START, "analyze_task")
        workflow.add_edge("analyze_task", "select_lane")
        workflow.add_edge("select_lane", "route_service")
        workflow.add_edge("route_service", "setup_worktree")
        workflow.add_conditional_edges(
            "setup_worktree",
            self._should_approve_cost,
            {
                "approve": "cost_approval",
                "skip": "execute_task"
            }
        )
        workflow.add_edge("cost_approval", "execute_task")
        workflow.add_edge("execute_task", "commit_changes")
        workflow.add_edge("commit_changes", "update_metrics")
        workflow.add_edge("update_metrics", END)
        
        return workflow.compile()
    
    async def _analyze_task(self, state: DevWorkflowState) -> DevWorkflowState:
        """Analyze task complexity"""
        analyzer = TaskComplexityAnalyzer()
        complexity = analyzer.classify_complexity(state.task_description)
        state.complexity = complexity
        return state
    
    async def _select_lane(self, state: DevWorkflowState) -> DevWorkflowState:
        """Select appropriate git lane for the task"""
        if self.git_manager:
            lane = self.service_router.select_lane_for_task(state.task_description)
            state.selected_lane = lane
            if lane and lane in self.git_manager.lanes:
                lane_config = self.git_manager.lanes[lane]
                state.lane_config = {
                    "name": lane_config.name,
                    "worktree_path": lane_config.worktree_path,
                    "allowed_patterns": lane_config.allowed_patterns,
                    "agent_type": lane_config.agent_type
                }
        return state
    
    async def _route_service(self, state: DevWorkflowState) -> DevWorkflowState:
        """Route to optimal service considering git lane"""
        service, lane = await self.service_router.select_optimal_service(
            state.task_description,
            state.complexity,
            lane=state.selected_lane
        )
        state.selected_service = service
        state.cost_estimate = SERVICES[service].cost_per_request
        return state
    
    async def _setup_worktree(self, state: DevWorkflowState) -> DevWorkflowState:
        """Set up git worktree for the selected lane"""
        if (self.git_manager and state.selected_lane and 
            state.selected_lane in self.git_manager.lanes):
            
            lane_config = self.git_manager.lanes[state.selected_lane]
            worktree_path = Path(lane_config.worktree_path)
            
            # Ensure worktree exists
            if not worktree_path.exists():
                success = self.git_manager.create_worktree(lane_config)
                if not success:
                    console.print(f"⚠️  Warning: Could not create worktree for {state.selected_lane}")
            
            state.worktree_path = str(worktree_path)
            console.print(f"🌱 Using worktree: {state.worktree_path}")
        
        return state
    
    def _should_approve_cost(self, state: DevWorkflowState) -> str:
        """Determine if cost approval is needed"""
        return "approve" if state.cost_estimate > 0 else "skip"
    
    async def _cost_approval(self, state: DevWorkflowState) -> DevWorkflowState:
        """Handle cost approval process"""
        # In real implementation, this could trigger human-in-the-loop
        state.quota_approved = True
        return state
    
    async def _execute_task(self, state: DevWorkflowState) -> DevWorkflowState:
        """Execute the task using selected service in appropriate worktree"""
        # Set working directory to worktree if available
        original_cwd = None
        if state.worktree_path and Path(state.worktree_path).exists():
            original_cwd = os.getcwd()
            os.chdir(state.worktree_path)
            console.print(f"📁 Working in: {state.worktree_path}")
        
        try:
            result = await self.agent_crew.execute_research_plan_code_workflow(
                state.task_description,
                state.selected_service
            )
            
            # Add lane information to result
            if state.selected_lane:
                result['lane_used'] = state.selected_lane
                result['worktree_path'] = state.worktree_path
            
            state.results = result
            
        finally:
            # Restore original working directory
            if original_cwd:
                os.chdir(original_cwd)
        
        return state
    
    async def _commit_changes(self, state: DevWorkflowState) -> DevWorkflowState:
        """Commit changes to git if in a worktree"""
        if not state.worktree_path or not Path(state.worktree_path).exists():
            return state
        
        try:
            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "-C", state.worktree_path, "status", "--porcelain"],
                capture_output=True, text=True
            )
            
            if result.stdout.strip():  # There are changes
                # Add all changes
                subprocess.run(
                    ["git", "-C", state.worktree_path, "add", "."],
                    check=True
                )
                
                # Create commit message
                lane_prefix = state.selected_lane or "auto"
                commit_msg = f"{lane_prefix}: {state.task_description[:50]}..."
                
                # Commit changes
                subprocess.run(
                    ["git", "-C", state.worktree_path, "commit", "-m", commit_msg],
                    check=True
                )
                
                console.print(f"✅ Committed changes in {state.selected_lane} lane")
                state.results['committed'] = True
                state.results['commit_message'] = commit_msg
            
        except subprocess.CalledProcessError as e:
            console.print(f"⚠️  Could not commit changes: {e}")
            state.results['commit_error'] = str(e)
        
        return state
    
    async def _update_metrics(self, state: DevWorkflowState) -> DevWorkflowState:
        """Update usage metrics"""
        await self.service_router.quota_manager.update_usage(
            state.selected_service
        )
        return state
    
    async def execute_workflow(self, task_description: str, lane: Optional[str] = None) -> Dict[str, Any]:
        """Execute the complete workflow with optional lane specification"""
        initial_state = DevWorkflowState(
            task_description=task_description,
            selected_lane=lane
        )
        
        with TASK_DURATION.time():
            final_state = await self.workflow.ainvoke(initial_state)
        
        return final_state.results

class AgenticFrameworkOrchestrator:
    """Main orchestrator class with database integration"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", enable_git: bool = True, database_url: str = "sqlite:///./workflow_executions.db"):
        # Initialize database
        self.db = DatabaseManager(database_url)
        
        # Initialize git manager
        self.git_manager = GitLaneManager() if enable_git else None
        
        # Initialize core components
        self.quota_manager = CostOptimizedQuotaManager(redis_url)
        self.service_router = CostOptimizedServiceRouter(self.quota_manager, self.git_manager)
        self.agent_crew = DevAgentCrew()
        self.workflow_engine = LangGraphWorkflowEngine(
            self.service_router, 
            self.agent_crew,
            self.git_manager
        )
    
    async def initialize(self):
        """Initialize the framework"""
        await self.quota_manager.connect()
        
        # Initialize git lanes if git is enabled
        if self.git_manager:
            try:
                # This will create worktrees if they don't exist
                lane_status = self.git_manager.get_lane_status()
                console.print(f"🌱 Git integration initialized with {len(lane_status)} lanes")
            except Exception as e:
                console.print(f"⚠️  Git integration failed: {e}")
                self.git_manager = None
        
        console.print("🚀 Agentic Framework v3.0 initialized")
    
    async def execute_task(self, request: TaskRequest) -> Dict[str, Any]:
        """Execute a development task with database persistence"""
        console.print(f"📋 Executing task: {request.description}")
        
        start_time = datetime.utcnow()
        execution_record = None
        
        try:
            # Analyze task complexity first
            analyzer = TaskComplexityAnalyzer()
            complexity = request.complexity or analyzer.classify_complexity(request.description)
            
            # Determine service
            if request.force_agent:
                selected_service = request.force_agent
            else:
                selected_service, _ = await self.service_router.select_optimal_service(
                    request.description,
                    complexity,
                    lane=request.lane
                )
            
            # Create database record
            execution_record = self.db.create_execution(
                task_description=request.description,
                complexity=complexity,
                selected_service=selected_service
            )
            
            # Update status to in progress
            self.db.update_execution_status(execution_record.id, ExecutionStatus.IN_PROGRESS)
            
            # Execute the task
            if request.force_agent:
                # Override service selection
                result = await self.agent_crew.execute_research_plan_code_workflow(
                    request.description,
                    request.force_agent
                )
            else:
                # Use workflow engine with lane support
                result = await self.workflow_engine.execute_workflow(
                    request.description, 
                    request.lane
                )
            
            # Update database with results
            self.db.update_execution_results(execution_record.id, result)
            self.db.update_execution_status(execution_record.id, ExecutionStatus.COMPLETED)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "completed",
                "task": request.description,
                "result": result,
                "execution_time": execution_time,
                "execution_id": execution_record.id,
                "database_record": True
            }
            
        except Exception as e:
            logger.error("task_execution_failed", error=str(e))
            
            # Update database with failure
            if execution_record:
                error_result = {"error": str(e)}
                self.db.update_execution_results(execution_record.id, error_result)
                self.db.update_execution_status(execution_record.id, ExecutionStatus.FAILED)
            
            return {
                "status": "failed",
                "task": request.description,
                "error": str(e),
                "execution_time": (datetime.utcnow() - start_time).total_seconds(),
                "execution_id": execution_record.id if execution_record else None,
                "database_record": execution_record is not None
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            "services": {},
            "total_cost_today": 0.0,
            "system_health": "healthy"
        }
        
        for service, config in SERVICES.items():
            usage = await self.quota_manager.get_daily_usage(service)
            cost = usage * config.cost_per_request
            status["total_cost_today"] += cost
            
            if config.daily_limit == 999999:
                usage_pct = 0.0
                status_text = f"{usage} requests (unlimited)"
            else:
                usage_pct = (usage / config.daily_limit) * 100
                status_text = f"{usage}/{config.daily_limit} ({usage_pct:.1f}%)"
            
            status["services"][service.value] = {
                "usage": usage,
                "limit": config.daily_limit,
                "cost_today": cost,
                "status": status_text,
                "available": usage < config.daily_limit
            }
        
        return status

# FastAPI Application
app = FastAPI(title="Agentic Framework v3.0", version="3.0.0")
orchestrator = AgenticFrameworkOrchestrator()

@app.on_event("startup")
async def startup():
    await orchestrator.initialize()

@app.post("/execute-task")
async def api_execute_task(
    request: TaskRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Execute a task via API"""
    result = await orchestrator.execute_task(request)
    return result

@app.get("/status")
async def api_get_status() -> Dict[str, Any]:
    """Get system status with database stats"""
    return await orchestrator.get_system_status()

@app.get("/executions/{execution_id}")
async def api_get_execution(execution_id: int) -> Dict[str, Any]:
    """Get execution details by ID"""
    execution = orchestrator.db.get_execution(execution_id)
    if execution:
        return {
            "id": execution.id,
            "workflow_id": execution.workflow_id,
            "task_description": execution.task_description,
            "complexity": execution.complexity,
            "selected_service": execution.selected_service,
            "status": execution.status,
            "cost_estimate": execution.cost_estimate,
            "actual_cost": execution.actual_cost,
            "start_time": execution.start_time.isoformat(),
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "selected_lane": execution.selected_lane,
            "committed": execution.committed
        }
    else:
        return {"error": "Execution not found"}

@app.get("/daily-stats")
async def api_get_daily_stats(date: Optional[str] = None) -> Dict[str, Any]:
    """Get daily execution statistics"""
    if date:
        from datetime import datetime
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}
    else:
        date_obj = None
    
    return orchestrator.db.get_daily_stats(date_obj)

# Typer CLI Application
cli_app = typer.Typer(help="Agentic Framework v3.0 CLI")

@cli_app.command()
def execute(
    description: str = typer.Argument(..., help="Task description"),
    force_agent: Optional[ServiceType] = typer.Option(None, help="Force specific agent"),
    max_cost: Optional[float] = typer.Option(None, help="Maximum cost limit"),
    lane: Optional[str] = typer.Option(None, help="Git lane to use")
):
    """Execute a development task"""
    async def _execute():
        orch = AgenticFrameworkOrchestrator()
        await orch.initialize()
        
        request = TaskRequest(
            description=description,
            force_agent=force_agent,
            max_cost=max_cost,
            lane=lane
        )
        
        with Progress() as progress:
            task = progress.add_task("Executing task...", total=100)
            
            result = await orch.execute_task(request)
            progress.advance(task, 100)
        
        if result["status"] == "completed":
            console.print("✅ Task completed successfully!")
            console.print(f"🎯 Service used: {result['result']['service_used']}")
            console.print(f"⏱️  Execution time: {result['execution_time']:.2f}s")
            if result.get('database_record'):
                console.print(f"💾 Database record: {result['execution_id']}")
        else:
            console.print(f"❌ Task failed: {result.get('error', 'Unknown error')}")
            if result.get('database_record'):
                console.print(f"💾 Error logged: {result['execution_id']}")
    
    asyncio.run(_execute())

@cli_app.command()
def status():
    """Show system status and quotas"""
    async def _status():
        orch = AgenticFrameworkOrchestrator()
        await orch.initialize()
        
        status = await orch.get_system_status()
        
        table = Table(title="System Status")
        table.add_column("Service", style="cyan")
        table.add_column("Usage", style="magenta")
        table.add_column("Cost Today", style="green")
        table.add_column("Status", style="yellow")
        
        for service_name, info in status["services"].items():
            table.add_row(
                service_name,
                str(info["usage"]),
                f"${info['cost_today']:.2f}",
                "🟢 Available" if info["available"] else "🔴 Limited"
            )
        
        console.print(table)
        console.print(f"\n💰 Total cost today: ${status['total_cost_today']:.2f}")
        console.print(f"📈 Monthly projection: ${status['total_cost_today'] * 30:.2f}")
        
        # Show database stats if available
        if 'daily_stats' in status and status['daily_stats']['total_executions'] > 0:
            stats = status['daily_stats']
            console.print(f"\n📊 Daily execution stats:")
            console.print(f"  Total executions: {stats['total_executions']}")
            console.print(f"  Average duration: {stats['average_duration']:.1f}s")
            console.print(f"  Success rate: {stats['by_status'].get('completed', 0) / stats['total_executions'] * 100:.1f}%")
    
    asyncio.run(_status())

@cli_app.command()
def history(
    limit: int = typer.Option(10, help="Number of recent executions to show"),
    service: Optional[ServiceType] = typer.Option(None, help="Filter by service")
):
    """Show execution history"""
    async def _history():
        orch = AgenticFrameworkOrchestrator()
        await orch.initialize()
        
        if service:
            executions = orch.db.get_executions_by_service(service, limit)
            title = f"Recent {service.value} Executions"
        else:
            # Get recent executions for all services
            from sqlmodel import select
            with Session(orch.db.engine) as session:
                statement = (select(WorkflowExecution)
                            .order_by(WorkflowExecution.start_time.desc())
                            .limit(limit))
                executions = list(session.exec(statement))
            title = "Recent Executions"
        
        if not executions:
            console.print("ℹ️  No executions found")
            return
        
        table = Table(title=title)
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Task", style="magenta", width=40)
        table.add_column("Service", style="green", width=12)
        table.add_column("Status", style="yellow", width=10)
        table.add_column("Cost", style="red", width=8)
        table.add_column("Time", style="blue", width=12)
        
        for execution in executions:
            # Truncate long task descriptions
            task = execution.task_description
            if len(task) > 37:
                task = task[:37] + "..."
            
            # Status emoji
            status_emoji = {
                "completed": "✅",
                "failed": "❌",
                "in_progress": "🔄",
                "pending": "⏳"
            }
            status = f"{status_emoji.get(execution.status.value, '')} {execution.status.value}"
            
            table.add_row(
                str(execution.id),
                task,
                execution.selected_service.value,
                status,
                f"${execution.actual_cost:.2f}",
                execution.start_time.strftime("%H:%M:%S")
            )
        
        console.print(table)
    
    asyncio.run(_history())

@cli_app.command()
def analyze(task_description: str = typer.Argument(..., help="Task to analyze")):
    """Analyze task complexity and recommend service"""
    analyzer = TaskComplexityAnalyzer()
    complexity = analyzer.classify_complexity(task_description)
    
    # Show complexity analysis
    console.print("🎯 Task Analysis:")
    console.print(f"  Description: {task_description}")
    console.print(f"  Complexity: [bold]{complexity.value}[/bold]")
    
    # Show matching services
    matching_services = [
        service for service, config in SERVICES.items()
        if complexity.value in config.complexity_match
    ]
    
    console.print("  Compatible services:")
    for service in sorted(matching_services, key=lambda s: SERVICES[s].priority):
        config = SERVICES[service]
        console.print(f"    - {service.value}: ${config.cost_per_request:.2f}/request")

@cli_app.command()
def lanes():
    """Show git lane status"""
    async def _lanes():
        orch = AgenticFrameworkOrchestrator()
        await orch.initialize()
        
        if not orch.git_manager:
            console.print("⚠️  Git integration not available")
            return
        
        status = orch.git_manager.get_lane_status()
        
        table = Table(title="Git Lane Status")
        table.add_column("Lane", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Branch", style="green")
        table.add_column("Changes", style="yellow")
        
        for lane_name, info in status.items():
            table.add_row(
                lane_name,
                info["status"],
                info.get("branch", "N/A"),
                info.get("changes", "N/A")
            )
        
        console.print(table)
    
    asyncio.run(_lanes())

@cli_app.command()
def open_lane(
    lane_name: str = typer.Argument(..., help="Lane name to open")
):
    """Open a git lane in VS Code"""
    async def _open_lane():
        orch = AgenticFrameworkOrchestrator()
        await orch.initialize()
        
        result = await orch.open_lane_in_vscode(lane_name)
        
        if result.get("success"):
            console.print(f"✅ {result['message']}")
            console.print(f"📁 Path: {result['path']}")
        else:
            console.print(f"❌ {result.get('error', 'Unknown error')}")
    
    asyncio.run(_open_lane())

if __name__ == "__main__":
    cli_app()