#!/usr/bin/env python3
"""
LangGraph Multi-Agent CLI - Replaces the entire PowerShell orchestrator
Cost-optimized agent routing with built-in quota management
"""

import asyncio
from typing import Literal, Dict, Any, List
from dataclasses import dataclass
import click
import json
from pathlib import Path

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import Ollama

# Your exact cost configuration from the PowerShell script
@dataclass
class ServiceConfig:
    daily_limit: int
    cost_per_request: float
    priority: int
    complexity_match: List[str]

SERVICES = {
    "gemini_cli": ServiceConfig(1000, 0.0, 1, ["simple", "moderate"]),
    "claude_code": ServiceConfig(25, 0.15, 2, ["complex"]),
    "aider_local": ServiceConfig(999999, 0.0, 3, ["moderate"]),
    "ollama_local": ServiceConfig(999999, 0.0, 4, ["simple", "moderate", "complex"])
}

class AgentState(MessagesState):
    """Extended state with cost tracking and task classification"""
    task_complexity: str = "simple"
    selected_agent: str = ""
    cost_estimate: float = 0.0
    usage_today: Dict[str, int] = {}

class CostOptimizedOrchestrator:
    def __init__(self):
        self.quota_file = Path(".ai/quota-tracker.json")
        self.usage_today = self.load_usage()
        
        # Initialize your agents (same as your PowerShell config)
        self.agents = {
            "gemini": create_react_agent(
                ChatGoogleGenerativeAI(model="gemini-1.5-pro"),
                tools=[],  # Add your tools here
                state_modifier="You are a cost-efficient agent for simple tasks"
            ),
            "claude": create_react_agent(
                ChatAnthropic(model="claude-3-sonnet-20240229"),
                tools=[],
                state_modifier="You are an expert agent for complex architectural tasks"
            ),
            "ollama": create_react_agent(
                Ollama(model="codellama:7b-instruct"),
                tools=[],
                state_modifier="You are a local agent for development tasks"
            )
        }
        
        # Create the supervisor graph
        self.graph = self.build_graph()

    def load_usage(self) -> Dict[str, int]:
        """Load today's quota usage (replaces PowerShell quota tracking)"""
        if self.quota_file.exists():
            data = json.loads(self.quota_file.read_text())
            today = str(Path().cwd())  # Simplified - use proper date
            return data.get("services", {})
        return {}

    def classify_task_complexity(self, task: str) -> str:
        """Your exact task classification logic from PowerShell"""
        complex_keywords = [
            "architecture", "redesign", "refactor large", "performance", 
            "security audit", "database migration", "infrastructure"
        ]
        moderate_keywords = [
            "feature", "implement", "add component", "API", "integration"
        ]
        
        task_lower = task.lower()
        if any(keyword in task_lower for keyword in complex_keywords):
            return "complex"
        elif any(keyword in task_lower for keyword in moderate_keywords):
            return "moderate"
        return "simple"

    def select_optimal_agent(self, complexity: str) -> str:
        """Cost-aware agent selection (replaces your PowerShell logic)"""
        for service_name, config in SERVICES.items():
            if complexity not in config.complexity_match:
                continue
                
            usage = self.usage_today.get(service_name, 0)
            if usage < config.daily_limit:
                # Check cost warnings for premium services
                if service_name == "claude_code" and usage > config.daily_limit * 0.6:
                    print(f"⚠️  Claude Code usage at {usage}/{config.daily_limit}")
                    print(f"💰 Cost today: ${usage * config.cost_per_request:.2f}")
                    if not click.confirm("Continue with Claude Code?"):
                        continue
                
                print(f"🎯 Selected: {service_name} (Usage: {usage}/{config.daily_limit})")
                return service_name.replace("_cli", "").replace("_local", "")
        
        print("⚠️  All quotas exceeded, using local")
        return "ollama"

    def build_graph(self) -> StateGraph:
        """Create the multi-agent workflow graph"""
        
        def analyze_task(state: AgentState) -> AgentState:
            """Task analysis node (replaces PowerShell complexity assessment)"""
            messages = state["messages"]
            last_message = messages[-1].content if messages else ""
            
            complexity = self.classify_task_complexity(last_message)
            selected_agent = self.select_optimal_agent(complexity)
            
            return {
                "task_complexity": complexity,
                "selected_agent": selected_agent,
                "cost_estimate": SERVICES.get(f"{selected_agent}_cli", 
                                           SERVICES[f"{selected_agent}_local"]).cost_per_request
            }

        def route_to_agent(state: AgentState) -> Literal["gemini", "claude", "ollama"]:
            """Dynamic routing based on cost optimization"""
            return state["selected_agent"]

        def update_usage(state: AgentState) -> AgentState:
            """Update quota usage (replaces PowerShell quota management)"""
            agent = state["selected_agent"]
            service_key = f"{agent}_cli" if agent != "ollama" else f"{agent}_local"
            
            self.usage_today[service_key] = self.usage_today.get(service_key, 0) + 1
            
            # Save usage
            self.quota_file.parent.mkdir(exist_ok=True)
            self.quota_file.write_text(json.dumps({
                "lastReset": "2025-01-01",  # Use proper date logic
                "services": self.usage_today
            }, indent=2))
            
            return state

        # Build the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze", analyze_task)
        workflow.add_node("gemini", self.agents["gemini"])
        workflow.add_node("claude", self.agents["claude"])
        workflow.add_node("ollama", self.agents["ollama"])
        workflow.add_node("update_usage", update_usage)
        
        # Add routing logic
        workflow.add_edge(START, "analyze")
        workflow.add_conditional_edges("analyze", route_to_agent)
        workflow.add_edge("gemini", "update_usage")
        workflow.add_edge("claude", "update_usage")
        workflow.add_edge("ollama", "update_usage")
        workflow.add_edge("update_usage", END)
        
        # Add persistence (replaces your SQLite state management)
        memory = SqliteSaver.from_conn_string(":memory:")
        return workflow.compile(checkpointer=memory)

    async def execute_task(self, task: str) -> Dict[str, Any]:
        """Execute task with cost optimization"""
        config = {"configurable": {"thread_id": "main"}}
        
        result = await self.graph.ainvoke(
            {"messages": [HumanMessage(content=task)]},
            config=config
        )
        
        return {
            "success": True,
            "agent_used": result["selected_agent"],
            "complexity": result["task_complexity"],
            "cost": result["cost_estimate"],
            "output": result["messages"][-1].content
        }

# CLI Interface (replaces your Python CLI module)
@click.group()
def cli():
    """Multi-Agent Development Framework CLI"""
    pass

@cli.command()
@click.argument('task')
@click.option('--force-agent', type=click.Choice(['gemini', 'claude', 'ollama']))
async def execute(task: str, force_agent: str = None):
    """Execute a development task with optimal agent selection"""
    orchestrator = CostOptimizedOrchestrator()
    
    if force_agent:
        # Override agent selection
        orchestrator.usage_today[f"{force_agent}_cli"] = 0
    
    result = await orchestrator.execute_task(task)
    
    print(f"✅ Task completed by {result['agent_used']}")
    print(f"🎯 Complexity: {result['complexity']}")
    print(f"💰 Cost: ${result['cost']:.2f}")
    print(f"📄 Result: {result['output']}")

@cli.command()
def status():
    """Show framework status (replaces PowerShell status command)"""
    orchestrator = CostOptimizedOrchestrator()
    usage = orchestrator.usage_today
    
    print("📊 Framework Status")
    print("==================")
    
    total_cost = 0
    for service_name, config in SERVICES.items():
        current_usage = usage.get(service_name, 0)
        cost = current_usage * config.cost_per_request
        total_cost += cost
        
        if config.daily_limit == 999999:
            status_text = f"{current_usage} requests (unlimited)"
        else:
            pct = (current_usage / config.daily_limit) * 100
            status_text = f"{current_usage}/{config.daily_limit} ({pct:.1f}%)"
        
        print(f"  {service_name}: {status_text} - ${cost:.2f}")
    
    print(f"\n💰 Total cost today: ${total_cost:.2f}")
    print(f"📈 Monthly projection: ${total_cost * 30:.2f}")

@cli.command()
@click.argument('task_description')
def analyze(task_description: str):
    """Analyze task complexity and recommend agent"""
    orchestrator = CostOptimizedOrchestrator()
    complexity = orchestrator.classify_task_complexity(task_description)
    agent = orchestrator.select_optimal_agent(complexity)
    
    print(f"🎯 Task Analysis:")
    print(f"  Complexity: {complexity}")
    print(f"  Recommended Agent: {agent}")
    print(f"  Estimated Cost: ${SERVICES.get(f'{agent}_cli', SERVICES[f'{agent}_local']).cost_per_request:.2f}")

if __name__ == "__main__":
    cli()
