#!/usr/bin/env python3
"""
MOD-010: Automated Merge Strategy
Cost-aware merge tool selection and conflict resolution
"""

import asyncio
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
import subprocess
import re
import yaml

import lib.cost_tracker as cost_tracker
import lib.audit_logger as audit_logger

# Simple mock classes for components that don't exist as classes
class ToolHealthTracker:
    def get_health_score(self, tool_name: str) -> float:
        return 0.8
    
    def record_success(self, tool_name: str, duration: float):
        pass
    
    def record_failure(self, tool_name: str):
        pass

class CircuitBreaker:
    def __init__(self, tool_name: str, failure_threshold: float = 0.3, recovery_timeout: int = 300):
        self.tool_name = tool_name
        
    def can_execute(self) -> bool:
        return True
        
    def record_success(self):
        pass
        
    def record_failure(self):
        pass


class MergeStrategy(str, Enum):
    """Available merge strategies"""
    AUTO_MERGE = "auto_merge"
    THREE_WAY = "three_way" 
    AI_ASSISTED = "ai_assisted"
    MANUAL_REVIEW = "manual_review"
    CONFLICT_FREE = "conflict_free"


class MergeToolType(str, Enum):
    """Available merge tools"""
    GIT_NATIVE = "git_native"
    VSCODE_MERGE = "vscode_merge"
    CLAUDE_CODE = "claude_code"
    GEMINI_CLI = "gemini_cli"  
    AIDER_LOCAL = "aider_local"
    MANUAL_EDITOR = "manual_editor"


class ConflictComplexity(str, Enum):
    """Conflict complexity levels"""
    NONE = "none"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


@dataclass
class MergeConflict:
    """Represents a merge conflict"""
    file_path: str
    conflict_type: str
    complexity: ConflictComplexity
    line_count: int
    context_lines: List[str]
    base_content: str
    current_content: str
    incoming_content: str
    
    
@dataclass
class MergeToolConfig:
    """Configuration for merge tools"""
    name: str
    tool_type: MergeToolType
    cost_per_use: float
    complexity_support: List[ConflictComplexity]
    max_file_size: int  # in lines
    timeout_seconds: int
    success_rate: float
    availability_check: callable
    

class AutomatedMergeStrategy:
    """
    MOD-010: Automated Merge Strategy Implementation
    
    Intelligently selects merge tools based on:
    - Conflict complexity analysis
    - Cost optimization preferences 
    - Tool availability and health
    - Success rate historical data
    - Budget constraints
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/merge_strategy.yaml"
        self.health_tracker = ToolHealthTracker()
        
        self.merge_tools = self._load_merge_tools()
        self.strategy_rules = self._load_strategy_rules()
        
        # Circuit breakers for each tool
        self.circuit_breakers = {
            tool.name: CircuitBreaker(
                tool.name, 
                failure_threshold=0.3,
                recovery_timeout=300
            )
            for tool in self.merge_tools.values()
        }
        
    def _load_merge_tools(self) -> Dict[str, MergeToolConfig]:
        """Load merge tool configurations"""
        return {
            "git_native": MergeToolConfig(
                name="git_native",
                tool_type=MergeToolType.GIT_NATIVE,
                cost_per_use=0.0,
                complexity_support=[ConflictComplexity.NONE, ConflictComplexity.SIMPLE],
                max_file_size=1000,
                timeout_seconds=30,
                success_rate=0.95,
                availability_check=self._check_git_available
            ),
            "vscode_merge": MergeToolConfig(
                name="vscode_merge",
                tool_type=MergeToolType.VSCODE_MERGE,
                cost_per_use=0.0,
                complexity_support=[ConflictComplexity.SIMPLE, ConflictComplexity.MODERATE],
                max_file_size=2000,
                timeout_seconds=300,
                success_rate=0.85,
                availability_check=self._check_vscode_available
            ),
            "claude_code": MergeToolConfig(
                name="claude_code", 
                tool_type=MergeToolType.CLAUDE_CODE,
                cost_per_use=0.15,
                complexity_support=[ConflictComplexity.MODERATE, ConflictComplexity.COMPLEX, ConflictComplexity.CRITICAL],
                max_file_size=5000,
                timeout_seconds=120,
                success_rate=0.92,
                availability_check=self._check_claude_available
            ),
            "gemini_cli": MergeToolConfig(
                name="gemini_cli",
                tool_type=MergeToolType.GEMINI_CLI,
                cost_per_use=0.02,
                complexity_support=[ConflictComplexity.SIMPLE, ConflictComplexity.MODERATE],
                max_file_size=3000,
                timeout_seconds=60,
                success_rate=0.80,
                availability_check=self._check_gemini_available
            ),
            "aider_local": MergeToolConfig(
                name="aider_local",
                tool_type=MergeToolType.AIDER_LOCAL,
                cost_per_use=0.0,
                complexity_support=[ConflictComplexity.SIMPLE, ConflictComplexity.MODERATE, ConflictComplexity.COMPLEX],
                max_file_size=4000,
                timeout_seconds=180,
                success_rate=0.78,
                availability_check=self._check_aider_available
            ),
            "manual_editor": MergeToolConfig(
                name="manual_editor",
                tool_type=MergeToolType.MANUAL_EDITOR,
                cost_per_use=0.0,
                complexity_support=list(ConflictComplexity),
                max_file_size=float('inf'),
                timeout_seconds=float('inf'),
                success_rate=0.70,  # Assumes manual intervention
                availability_check=lambda: True
            )
        }
    
    def _load_strategy_rules(self) -> Dict[str, Any]:
        """Load merge strategy decision rules"""
        return {
            "cost_optimization": {
                "prefer_free_tools": True,
                "max_cost_per_merge": 0.50,
                "budget_threshold_warning": 0.80
            },
            "complexity_thresholds": {
                "simple_max_lines": 50,
                "moderate_max_lines": 200,
                "complex_max_lines": 500
            },
            "tool_selection_priorities": {
                ConflictComplexity.NONE: ["git_native"],
                ConflictComplexity.SIMPLE: ["git_native", "vscode_merge", "gemini_cli", "aider_local"],
                ConflictComplexity.MODERATE: ["vscode_merge", "gemini_cli", "aider_local", "claude_code"],
                ConflictComplexity.COMPLEX: ["claude_code", "aider_local", "vscode_merge"],
                ConflictComplexity.CRITICAL: ["claude_code", "manual_editor"]
            },
            "fallback_chains": {
                "claude_code": ["aider_local", "vscode_merge", "manual_editor"],
                "gemini_cli": ["aider_local", "vscode_merge", "manual_editor"],
                "aider_local": ["vscode_merge", "manual_editor"],
                "vscode_merge": ["manual_editor"],
                "git_native": ["vscode_merge", "manual_editor"]
            }
        }
    
    async def analyze_merge_conflicts(self, base_branch: str, feature_branch: str) -> List[MergeConflict]:
        """Analyze merge conflicts between branches"""
        conflicts = []
        
        try:
            # Perform a test merge to identify conflicts
            result = subprocess.run([
                "git", "merge-tree", base_branch, feature_branch
            ], capture_output=True, text=True, check=False)
            
            if result.returncode != 0 or "conflict" in result.stdout.lower():
                conflicts = await self._parse_merge_conflicts(result.stdout)
                
            audit_logger.log_action(
                f"merge_analysis_{base_branch}_{feature_branch}",
                "analysis",
                "conflict_analysis",
                {
                    "base_branch": base_branch,
                    "feature_branch": feature_branch,
                    "conflicts_found": len(conflicts),
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            audit_logger.log_action(
                f"merge_analysis_{base_branch}_{feature_branch}",
                "analysis",
                "error",
                {
                    "error": str(e),
                    "base_branch": base_branch,
                    "feature_branch": feature_branch
                }
            )
            
        return conflicts
    
    async def _parse_merge_conflicts(self, merge_output: str) -> List[MergeConflict]:
        """Parse git merge-tree output to extract conflicts"""
        conflicts = []
        
        # Parse the merge-tree output for conflict markers
        conflict_pattern = re.compile(r'<<<<<<< (.+?)\n(.*?)\n======\n(.*?)\n>>>>>>> (.+?)\n', re.DOTALL)
        
        for match in conflict_pattern.finditer(merge_output):
            current_content = match.group(2).strip()
            incoming_content = match.group(3).strip()
            
            # Determine conflict complexity based on content analysis
            complexity = self._assess_conflict_complexity(current_content, incoming_content)
            
            conflict = MergeConflict(
                file_path="unknown",  # Would need additional parsing
                conflict_type="content_conflict",
                complexity=complexity,
                line_count=len(current_content.split('\n')) + len(incoming_content.split('\n')),
                context_lines=[],
                base_content="",
                current_content=current_content,
                incoming_content=incoming_content
            )
            conflicts.append(conflict)
            
        return conflicts
    
    def _assess_conflict_complexity(self, current: str, incoming: str) -> ConflictComplexity:
        """Assess the complexity of a merge conflict"""
        # Simple heuristics for complexity assessment
        total_lines = len(current.split('\n')) + len(incoming.split('\n'))
        
        # Check for complex patterns
        complex_patterns = [
            r'class\s+\w+',  # Class definitions
            r'def\s+\w+\(',  # Function definitions
            r'import\s+\w+', # Import statements
            r'\{\s*".*":', # JSON/dict structures
            r'@\w+',  # Decorators
        ]
        
        complexity_score = 0
        combined_content = current + incoming
        
        for pattern in complex_patterns:
            complexity_score += len(re.findall(pattern, combined_content))
        
        # Complexity classification
        if total_lines > self.strategy_rules["complexity_thresholds"]["complex_max_lines"]:
            return ConflictComplexity.CRITICAL
        elif total_lines > self.strategy_rules["complexity_thresholds"]["moderate_max_lines"] or complexity_score > 5:
            return ConflictComplexity.COMPLEX
        elif total_lines > self.strategy_rules["complexity_thresholds"]["simple_max_lines"] or complexity_score > 2:
            return ConflictComplexity.MODERATE
        else:
            return ConflictComplexity.SIMPLE
    
    async def select_optimal_merge_tool(self, conflicts: List[MergeConflict]) -> Tuple[str, MergeStrategy]:
        """Select the optimal merge tool based on conflicts and constraints"""
        
        if not conflicts:
            return "git_native", MergeStrategy.AUTO_MERGE
        
        # Determine overall complexity
        max_complexity = max((c.complexity for c in conflicts), default=ConflictComplexity.SIMPLE)
        total_cost_estimate = 0.0
        
        # Get prioritized tool list for this complexity
        candidate_tools = self.strategy_rules["tool_selection_priorities"][max_complexity]
        
        # Filter by availability and health
        available_tools = []
        for tool_name in candidate_tools:
            tool = self.merge_tools[tool_name]
            
            # Check availability
            if not tool.availability_check():
                continue
                
            # Check circuit breaker
            if not self.circuit_breakers[tool_name].can_execute():
                continue
                
            # Check health score
            health_score = self.health_tracker.get_health_score(tool_name)
            if health_score < 0.5:
                continue
                
            available_tools.append((tool_name, tool))
        
        if not available_tools:
            # Fallback to manual editor
            return "manual_editor", MergeStrategy.MANUAL_REVIEW
        
        # Cost-aware selection (simplified for demo)
        remaining_budget = 10.0
        
        # Select the best tool considering cost and capability
        selected_tool = None
        for tool_name, tool in available_tools:
            estimated_cost = tool.cost_per_use * len(conflicts)
            
            # Skip if too expensive
            if estimated_cost > remaining_budget:
                continue
                
            # Skip if exceeds max cost per merge
            max_cost = self.strategy_rules["cost_optimization"]["max_cost_per_merge"]
            if estimated_cost > max_cost and self.strategy_rules["cost_optimization"]["prefer_free_tools"]:
                continue
            
            # This tool is acceptable
            selected_tool = tool_name
            total_cost_estimate = estimated_cost
            break
        
        if not selected_tool:
            # Fallback to free tools only
            free_tools = [(name, tool) for name, tool in available_tools if tool.cost_per_use == 0.0]
            if free_tools:
                selected_tool = free_tools[0][0]
            else:
                selected_tool = "manual_editor"
        
        # Determine merge strategy
        strategy = self._determine_merge_strategy(selected_tool, max_complexity)
        
        # Log the selection
        audit_logger.log_action(
            f"tool_selection_{selected_tool}",
            "selection",
            "merge_tool_selection",
            {
                "selected_tool": selected_tool,
                "merge_strategy": strategy.value,
                "conflict_complexity": max_complexity.value,
                "conflicts_count": len(conflicts),
                "estimated_cost": total_cost_estimate,
                "selection_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return selected_tool, strategy
    
    def _determine_merge_strategy(self, tool_name: str, complexity: ConflictComplexity) -> MergeStrategy:
        """Determine the merge strategy based on tool and complexity"""
        tool = self.merge_tools[tool_name]
        
        if tool.tool_type == MergeToolType.GIT_NATIVE:
            return MergeStrategy.AUTO_MERGE
        elif tool.tool_type in [MergeToolType.CLAUDE_CODE, MergeToolType.GEMINI_CLI, MergeToolType.AIDER_LOCAL]:
            return MergeStrategy.AI_ASSISTED
        elif tool.tool_type == MergeToolType.VSCODE_MERGE:
            return MergeStrategy.THREE_WAY
        else:
            return MergeStrategy.MANUAL_REVIEW
    
    async def execute_merge(self, tool_name: str, strategy: MergeStrategy, 
                          conflicts: List[MergeConflict], base_branch: str, 
                          feature_branch: str) -> Dict[str, Any]:
        """Execute the merge using the selected tool and strategy"""
        
        start_time = datetime.utcnow()
        tool = self.merge_tools[tool_name]
        
        try:
            # Record cost before execution
            if tool.cost_per_use > 0:
                estimated_cost = tool.cost_per_use * len(conflicts)
                cost_tracker.record_cost(
                    f"merge_operation_{tool_name}",
                    tool_name,
                    "merge_execution", 
                    len(conflicts),
                    estimated_cost
                )
            
            # Execute merge based on strategy
            result = await self._execute_merge_strategy(tool_name, strategy, base_branch, feature_branch)
            
            # Record success
            self.health_tracker.record_success(tool_name, 
                                             (datetime.utcnow() - start_time).total_seconds())
            self.circuit_breakers[tool_name].record_success()
            
            # Log execution
            audit_logger.log_action(
                f"merge_execution_{tool_name}",
                "execution",
                "merge_execution_success",
                {
                    "tool": tool_name,
                    "strategy": strategy.value,
                    "base_branch": base_branch,
                    "feature_branch": feature_branch,
                    "conflicts_resolved": len(conflicts),
                    "execution_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "success": True,
                "tool_used": tool_name,
                "strategy": strategy.value,
                "conflicts_resolved": len(conflicts),
                "execution_time": (datetime.utcnow() - start_time).total_seconds(),
                "result": result
            }
            
        except Exception as e:
            # Record failure
            self.health_tracker.record_failure(tool_name)
            self.circuit_breakers[tool_name].record_failure()
            
            # Log failure
            audit_logger.log_action(
                f"merge_execution_{tool_name}",
                "execution",
                "merge_execution_failure",
                {
                    "tool": tool_name,
                    "strategy": strategy.value,
                    "error": str(e),
                    "base_branch": base_branch,
                    "feature_branch": feature_branch,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Try fallback
            fallback_tools = self.strategy_rules["fallback_chains"].get(tool_name, [])
            if fallback_tools:
                fallback_tool = fallback_tools[0]
                audit_logger.log_action(
                    f"merge_fallback_{tool_name}",
                    "fallback",
                    "merge_fallback_triggered",
                    {
                        "original_tool": tool_name,
                        "fallback_tool": fallback_tool,
                        "reason": str(e)
                    }
                )
                
                # Recursive call with fallback tool
                fallback_strategy = self._determine_merge_strategy(
                    fallback_tool, 
                    max((c.complexity for c in conflicts), default=ConflictComplexity.SIMPLE)
                )
                return await self.execute_merge(fallback_tool, fallback_strategy, 
                                              conflicts, base_branch, feature_branch)
            
            return {
                "success": False,
                "tool_used": tool_name,
                "strategy": strategy.value,
                "error": str(e),
                "execution_time": (datetime.utcnow() - start_time).total_seconds()
            }
    
    async def _execute_merge_strategy(self, tool_name: str, strategy: MergeStrategy, 
                                    base_branch: str, feature_branch: str) -> str:
        """Execute the specific merge strategy"""
        
        if strategy == MergeStrategy.AUTO_MERGE:
            result = subprocess.run([
                "git", "merge", "--no-edit", feature_branch
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return "Auto-merge successful"
            else:
                raise Exception(f"Auto-merge failed: {result.stderr}")
        
        elif strategy == MergeStrategy.AI_ASSISTED:
            # For AI-assisted merges, we would integrate with the specific AI tool
            # This is a placeholder for the actual AI integration
            return await self._ai_assisted_merge(tool_name, base_branch, feature_branch)
        
        elif strategy == MergeStrategy.THREE_WAY:
            # Launch VS Code merge editor
            result = subprocess.run([
                "code", "--wait", "--merge", base_branch, feature_branch
            ], capture_output=True, text=True)
            return "Three-way merge completed via VS Code"
        
        else:  # MANUAL_REVIEW
            return "Manual review required - conflicts too complex for automated resolution"
    
    async def _ai_assisted_merge(self, tool_name: str, base_branch: str, feature_branch: str) -> str:
        """AI-assisted merge resolution"""
        # This would integrate with the specific AI service
        # For now, return a placeholder result
        return f"AI-assisted merge completed using {tool_name}"
    
    # Availability check methods
    def _check_git_available(self) -> bool:
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_vscode_available(self) -> bool:
        try:
            subprocess.run(["code", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_claude_available(self) -> bool:
        # Check if Claude Code is available (would need actual implementation)
        return True  # Placeholder
    
    def _check_gemini_available(self) -> bool:
        # Check if Gemini CLI is available
        return True  # Placeholder
    
    def _check_aider_available(self) -> bool:
        try:
            subprocess.run(["aider", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_merge_statistics(self) -> Dict[str, Any]:
        """Get merge operation statistics"""
        # This would return actual statistics from the audit log
        return {
            "total_merges": 0,
            "success_rate": 0.0,
            "average_cost": 0.0,
            "tool_usage": {},
            "complexity_distribution": {},
            "generated_at": datetime.utcnow().isoformat()
        }


async def main():
    """Example usage of the Automated Merge Strategy"""
    merge_strategy = AutomatedMergeStrategy()
    
    # Analyze conflicts
    conflicts = await merge_strategy.analyze_merge_conflicts("main", "feature-branch")
    print(f"Found {len(conflicts)} conflicts")
    
    # Select optimal tool
    tool, strategy = await merge_strategy.select_optimal_merge_tool(conflicts)
    print(f"Selected tool: {tool}, strategy: {strategy}")
    
    # Execute merge
    result = await merge_strategy.execute_merge(tool, strategy, conflicts, "main", "feature-branch")
    print(f"Merge result: {result}")


if __name__ == "__main__":
    asyncio.run(main())