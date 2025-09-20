#!/usr/bin/env python3
"""
Context Analysis Engine
Intelligent task interpretation and workflow suggestions
"""

import asyncio
import os
import json
import re
import ast
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum

import lib.cost_tracker as cost_tracker
import lib.audit_logger as audit_logger

# Simple mock class for ToolHealthTracker
class ToolHealthTracker:
    def get_health_score(self, tool_name: str) -> float:
        return 0.8


class TaskType(str, Enum):
    """Types of development tasks"""
    CODE_GENERATION = "code_generation"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    SECURITY_FIX = "security_fix"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    INTEGRATION = "integration"
    DEPLOYMENT = "deployment"
    CONFIGURATION = "configuration"
    ANALYSIS = "analysis"
    UNKNOWN = "unknown"


class Complexity(str, Enum):
    """Task complexity levels"""
    TRIVIAL = "trivial"      # < 1 hour
    SIMPLE = "simple"        # 1-4 hours
    MODERATE = "moderate"    # 4-16 hours
    COMPLEX = "complex"      # 16-40 hours
    CRITICAL = "critical"    # 40+ hours


class Priority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class Language(str, Enum):
    """Programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    SHELL = "shell"
    SQL = "sql"
    HTML = "html"
    CSS = "css"
    YAML = "yaml"
    JSON = "json"
    XML = "xml"
    MARKDOWN = "markdown"
    MQL4 = "mql4"
    POWERSHELL = "powershell"
    UNKNOWN = "unknown"


@dataclass
class FileContext:
    """Context information for a file"""
    path: str
    language: Language
    size_lines: int
    imports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    last_modified: Optional[datetime] = None
    complexity_score: float = 0.0
    test_coverage: float = 0.0
    

@dataclass
class ProjectContext:
    """Overall project context"""
    root_path: str
    project_type: str
    languages: Set[Language] = field(default_factory=set)
    frameworks: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    structure: Dict[str, Any] = field(default_factory=dict)
    test_framework: Optional[str] = None
    build_system: Optional[str] = None
    ci_cd: List[str] = field(default_factory=list)
    documentation_coverage: float = 0.0
    

@dataclass
class TaskContext:
    """Context analysis for a specific task"""
    description: str
    task_type: TaskType
    complexity: Complexity
    priority: Priority
    affected_files: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    estimated_effort_hours: float = 0.0
    risk_level: str = "medium"
    prerequisites: List[str] = field(default_factory=list)
    suggested_approach: str = ""
    

@dataclass
class WorkflowSuggestion:
    """Suggested workflow for a task"""
    name: str
    description: str
    steps: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    estimated_time_minutes: int = 0
    success_probability: float = 0.0
    risk_factors: List[str] = field(default_factory=list)
    

class ContextAnalysisEngine:
    """
    Intelligent task interpretation and workflow suggestions
    
    Analyzes:
    - Project structure and codebase context
    - Task requirements and complexity
    - Available tools and their capabilities
    - Historical success patterns
    - Cost-benefit optimization
    """
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd())
        self.health_tracker = ToolHealthTracker()
        
        # Cache for project analysis
        self._project_context_cache: Optional[ProjectContext] = None
        self._file_contexts_cache: Dict[str, FileContext] = {}
        
        # Pattern libraries for task classification
        self.task_patterns = self._load_task_patterns()
        self.complexity_indicators = self._load_complexity_indicators()
        self.workflow_templates = self._load_workflow_templates()
        
    def _load_task_patterns(self) -> Dict[TaskType, List[str]]:
        """Load patterns for task type classification"""
        return {
            TaskType.CODE_GENERATION: [
                r"implement|create|add|build|generate|write",
                r"new feature|functionality|component|module",
                r"from scratch|create new|build new"
            ],
            TaskType.BUG_FIX: [
                r"fix|resolve|debug|solve|repair",
                r"bug|error|issue|problem|defect",
                r"not working|broken|failing|incorrect"
            ],
            TaskType.REFACTORING: [
                r"refactor|cleanup|reorganize|restructure",
                r"improve|optimize|enhance|simplify",
                r"clean up|make better|modernize"
            ],
            TaskType.TESTING: [
                r"test|testing|unittest|integration test",
                r"coverage|test suite|test case",
                r"verify|validate|check"
            ],
            TaskType.DOCUMENTATION: [
                r"document|documentation|readme|docs",
                r"comment|explain|describe",
                r"api doc|user guide|tutorial"
            ],
            TaskType.SECURITY_FIX: [
                r"security|secure|vulnerability|exploit",
                r"authentication|authorization|permission",
                r"sanitize|validate input|escape"
            ],
            TaskType.PERFORMANCE_OPTIMIZATION: [
                r"performance|optimize|speed up|faster",
                r"memory|cpu|latency|throughput",
                r"cache|index|query optimization"
            ],
            TaskType.INTEGRATION: [
                r"integrate|connect|api|webhook",
                r"third party|external|service",
                r"sync|import|export"
            ],
            TaskType.DEPLOYMENT: [
                r"deploy|deployment|release|publish",
                r"docker|kubernetes|container",
                r"ci/cd|pipeline|automation"
            ],
            TaskType.CONFIGURATION: [
                r"config|configuration|setup|settings",
                r"environment|env|variable",
                r"yaml|json|toml|ini"
            ]
        }
    
    def _load_complexity_indicators(self) -> Dict[str, float]:
        """Load indicators for complexity assessment"""
        return {
            # High complexity indicators
            "distributed system": 3.0,
            "microservices": 2.5,
            "machine learning": 2.8,
            "real-time": 2.3,
            "concurrent": 2.2,
            "database migration": 2.0,
            "legacy code": 2.1,
            "integration": 1.8,
            "security": 2.0,
            "performance": 1.9,
            
            # Medium complexity indicators
            "api": 1.5,
            "authentication": 1.7,
            "testing": 1.3,
            "refactor": 1.4,
            "frontend": 1.2,
            "backend": 1.3,
            "database": 1.6,
            
            # Low complexity indicators
            "config": 0.8,
            "documentation": 0.6,
            "styling": 0.9,
            "logging": 0.7,
            "simple": 0.5,
            "basic": 0.6
        }
    
    def _load_workflow_templates(self) -> Dict[str, WorkflowSuggestion]:
        """Load predefined workflow templates"""
        return {
            "bug_fix_standard": WorkflowSuggestion(
                name="Standard Bug Fix Workflow",
                description="Systematic approach to identify and fix bugs",
                steps=[
                    "Reproduce the issue",
                    "Analyze error logs and stack traces", 
                    "Identify root cause",
                    "Implement fix with minimal changes",
                    "Add regression tests",
                    "Verify fix doesn't break existing functionality"
                ],
                tools=["git", "debugger", "testing_framework"],
                estimated_time_minutes=120,
                success_probability=0.85
            ),
            "feature_development": WorkflowSuggestion(
                name="Feature Development Workflow",
                description="End-to-end feature implementation",
                steps=[
                    "Analyze requirements and create design",
                    "Set up development environment",
                    "Implement core functionality",
                    "Add comprehensive tests",
                    "Update documentation",
                    "Code review and integration"
                ],
                tools=["ide", "testing_framework", "documentation_tool"],
                estimated_time_minutes=480,
                success_probability=0.75
            ),
            "refactoring_safe": WorkflowSuggestion(
                name="Safe Refactoring Workflow",
                description="Risk-minimized code refactoring approach",
                steps=[
                    "Ensure comprehensive test coverage",
                    "Create backup branch",
                    "Refactor in small, incremental steps",
                    "Run tests after each change",
                    "Update documentation as needed",
                    "Peer review before merging"
                ],
                tools=["testing_framework", "code_analysis"],
                estimated_time_minutes=240,
                success_probability=0.88
            )
        }
    
    async def analyze_project_context(self, force_refresh: bool = False) -> ProjectContext:
        """Analyze overall project context"""
        
        if self._project_context_cache and not force_refresh:
            return self._project_context_cache
        
        start_time = datetime.utcnow()
        
        project_context = ProjectContext(
            root_path=str(self.project_root),
            project_type="unknown"
        )
        
        try:
            # Analyze project structure
            await self._analyze_project_structure(project_context)
            
            # Detect languages and frameworks
            await self._detect_languages_and_frameworks(project_context)
            
            # Analyze dependencies
            await self._analyze_dependencies(project_context)
            
            # Detect build and CI/CD systems
            await self._detect_build_systems(project_context)
            
            # Cache the result
            self._project_context_cache = project_context
            
            # Log analysis
            audit_logger.log_action(
                f"project_analysis_{project_context.project_type}",
                "analysis",
                "project_context_analysis",
                {
                    "project_root": str(self.project_root),
                    "languages": list(project_context.languages),
                    "frameworks": project_context.frameworks,
                    "analysis_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            audit_logger.log_action(
                f"project_analysis_error",
                "analysis",
                "error",
                {
                    "error": str(e),
                    "project_root": str(self.project_root)
                }
            )
            
        return project_context
    
    async def _analyze_project_structure(self, context: ProjectContext):
        """Analyze project directory structure"""
        structure = {}
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]
            
            rel_path = os.path.relpath(root, self.project_root)
            if rel_path == '.':
                rel_path = 'root'
            
            structure[rel_path] = {
                'directories': dirs[:],
                'files': files[:50],  # Limit to avoid huge structures
                'file_count': len(files)
            }
        
        context.structure = structure
        
        # Determine project type based on structure
        if any('src' in dirs for dirs in structure.values()):
            context.project_type = "standard_src_layout"
        elif 'lib' in structure.get('root', {}).get('directories', []):
            context.project_type = "library_project"
        elif any(f.endswith('.py') for f in structure.get('root', {}).get('files', [])):
            context.project_type = "python_project"
        
    async def _detect_languages_and_frameworks(self, context: ProjectContext):
        """Detect programming languages and frameworks"""
        language_extensions = {
            '.py': Language.PYTHON,
            '.js': Language.JAVASCRIPT,
            '.ts': Language.TYPESCRIPT,
            '.java': Language.JAVA,
            '.cs': Language.CSHARP,
            '.cpp': Language.CPP,
            '.cc': Language.CPP,
            '.go': Language.GO,
            '.rs': Language.RUST,
            '.php': Language.PHP,
            '.rb': Language.RUBY,
            '.sh': Language.SHELL,
            '.sql': Language.SQL,
            '.html': Language.HTML,
            '.css': Language.CSS,
            '.yml': Language.YAML,
            '.yaml': Language.YAML,
            '.json': Language.JSON,
            '.xml': Language.XML,
            '.md': Language.MARKDOWN,
            '.mq4': Language.MQL4,
            '.ps1': Language.POWERSHELL
        }
        
        # Count files by extension
        extension_counts = {}
        for root, _, files in os.walk(self.project_root):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in language_extensions:
                    extension_counts[ext] = extension_counts.get(ext, 0) + 1
        
        # Add languages with significant presence
        for ext, count in extension_counts.items():
            if count >= 2:  # At least 2 files of this type
                context.languages.add(language_extensions[ext])
        
        # Detect frameworks based on files and dependencies
        framework_indicators = {
            'requirements.txt': ['flask', 'django', 'fastapi'],
            'package.json': ['react', 'vue', 'angular', 'express'],
            'pom.xml': ['spring', 'hibernate'],
            'Gemfile': ['rails', 'sinatra'],
            'composer.json': ['laravel', 'symfony']
        }
        
        for indicator_file, frameworks in framework_indicators.items():
            file_path = self.project_root / indicator_file
            if file_path.exists():
                try:
                    content = file_path.read_text().lower()
                    for framework in frameworks:
                        if framework in content:
                            context.frameworks.append(framework)
                except:
                    pass
    
    async def _analyze_dependencies(self, context: ProjectContext):
        """Analyze project dependencies"""
        dependency_files = {
            'requirements.txt': self._parse_requirements_txt,
            'package.json': self._parse_package_json,
            'Pipfile': self._parse_pipfile,
            'pyproject.toml': self._parse_pyproject_toml
        }
        
        for dep_file, parser in dependency_files.items():
            file_path = self.project_root / dep_file
            if file_path.exists():
                try:
                    deps = await parser(file_path)
                    context.dependencies.update(deps)
                except Exception as e:
                    continue
    
    async def _parse_requirements_txt(self, file_path: Path) -> Dict[str, str]:
        """Parse requirements.txt dependencies"""
        deps = {}
        content = file_path.read_text()
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                if '==' in line:
                    name, version = line.split('==', 1)
                    deps[name.strip()] = version.strip()
                elif '>=' in line:
                    name, version = line.split('>=', 1)
                    deps[name.strip()] = f">={version.strip()}"
                else:
                    deps[line] = "latest"
        return deps
    
    async def _parse_package_json(self, file_path: Path) -> Dict[str, str]:
        """Parse package.json dependencies"""
        try:
            content = json.loads(file_path.read_text())
            deps = {}
            deps.update(content.get('dependencies', {}))
            deps.update(content.get('devDependencies', {}))
            return deps
        except:
            return {}
    
    async def _parse_pipfile(self, file_path: Path) -> Dict[str, str]:
        """Parse Pipfile dependencies"""
        # Simplified TOML parsing for Pipfile
        deps = {}
        try:
            content = file_path.read_text()
            in_packages = False
            for line in content.splitlines():
                line = line.strip()
                if line == '[packages]':
                    in_packages = True
                elif line.startswith('[') and line != '[packages]':
                    in_packages = False
                elif in_packages and '=' in line:
                    name, version = line.split('=', 1)
                    deps[name.strip()] = version.strip(' "')
        except:
            pass
        return deps
    
    async def _parse_pyproject_toml(self, file_path: Path) -> Dict[str, str]:
        """Parse pyproject.toml dependencies"""
        # Basic TOML parsing for dependencies
        deps = {}
        try:
            content = file_path.read_text()
            # This is a simplified parser - in production, use a proper TOML library
            if 'dependencies' in content:
                # Extract dependencies section
                lines = content.splitlines()
                in_deps = False
                for line in lines:
                    line = line.strip()
                    if 'dependencies' in line and '[' in line:
                        in_deps = True
                    elif in_deps and line.startswith(']'):
                        break
                    elif in_deps and line and not line.startswith('#'):
                        # Parse dependency line
                        if '"' in line:
                            dep = line.strip(' ",')
                            if '>=' in dep or '==' in dep or '~=' in dep:
                                parts = re.split(r'[><=~!]+', dep)
                                if len(parts) >= 2:
                                    deps[parts[0].strip()] = dep[len(parts[0]):].strip()
                            else:
                                deps[dep] = "latest"
        except:
            pass
        return deps
    
    async def _detect_build_systems(self, context: ProjectContext):
        """Detect build and CI/CD systems"""
        build_indicators = {
            'Makefile': 'make',
            'setup.py': 'setuptools',
            'pyproject.toml': 'poetry/setuptools',
            'package.json': 'npm/yarn',
            'pom.xml': 'maven',
            'build.gradle': 'gradle',
            'CMakeLists.txt': 'cmake',
            'Cargo.toml': 'cargo'
        }
        
        for file, build_system in build_indicators.items():
            if (self.project_root / file).exists():
                context.build_system = build_system
                break
        
        # Detect CI/CD systems
        ci_indicators = {
            '.github/workflows': 'github_actions',
            '.gitlab-ci.yml': 'gitlab_ci',
            'Jenkinsfile': 'jenkins',
            '.travis.yml': 'travis_ci',
            'azure-pipelines.yml': 'azure_devops'
        }
        
        for indicator, ci_system in ci_indicators.items():
            if (self.project_root / indicator).exists():
                context.ci_cd.append(ci_system)
    
    async def analyze_task_context(self, task_description: str) -> TaskContext:
        """Analyze a specific task and provide context"""
        
        start_time = datetime.utcnow()
        
        # Initialize task context
        task_context = TaskContext(
            description=task_description,
            task_type=TaskType.UNKNOWN,
            complexity=Complexity.SIMPLE,
            priority=Priority.MEDIUM
        )
        
        try:
            # Classify task type
            task_context.task_type = await self._classify_task_type(task_description)
            
            # Assess complexity
            task_context.complexity = await self._assess_task_complexity(task_description)
            
            # Determine priority
            task_context.priority = await self._determine_task_priority(task_description)
            
            # Identify affected files
            task_context.affected_files = await self._identify_affected_files(task_description)
            
            # Estimate effort
            task_context.estimated_effort_hours = await self._estimate_effort(task_context)
            
            # Assess risk level
            task_context.risk_level = await self._assess_risk_level(task_context)
            
            # Generate suggested approach
            task_context.suggested_approach = await self._suggest_approach(task_context)
            
            # Log analysis
            audit_logger.log_action(
                f"task_analysis_{task_context.task_type.value}",
                "analysis",
                "task_context_analysis",
                {
                    "description": task_description,
                    "task_type": task_context.task_type.value,
                    "complexity": task_context.complexity.value,
                    "priority": task_context.priority.value,
                    "estimated_effort_hours": task_context.estimated_effort_hours,
                    "analysis_time_seconds": (datetime.utcnow() - start_time).total_seconds(),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            audit_logger.log_action(
                f"task_analysis_error",
                "analysis",
                "error",
                {
                    "error": str(e),
                    "description": task_description
                }
            )
        
        return task_context
    
    async def _classify_task_type(self, description: str) -> TaskType:
        """Classify the type of task based on description"""
        description_lower = description.lower()
        
        task_scores = {}
        for task_type, patterns in self.task_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, description_lower))
                score += matches
            task_scores[task_type] = score
        
        if task_scores:
            best_match = max(task_scores.items(), key=lambda x: x[1])
            if best_match[1] > 0:
                return best_match[0]
        
        return TaskType.UNKNOWN
    
    async def _assess_task_complexity(self, description: str) -> Complexity:
        """Assess task complexity based on description and indicators"""
        description_lower = description.lower()
        
        complexity_score = 1.0  # Base complexity
        
        # Apply complexity indicators
        for indicator, multiplier in self.complexity_indicators.items():
            if indicator in description_lower:
                complexity_score *= multiplier
        
        # Length-based complexity
        word_count = len(description.split())
        if word_count > 50:
            complexity_score *= 1.5
        elif word_count > 100:
            complexity_score *= 2.0
        
        # Map score to complexity enum
        if complexity_score < 0.8:
            return Complexity.TRIVIAL
        elif complexity_score < 1.5:
            return Complexity.SIMPLE
        elif complexity_score < 2.5:
            return Complexity.MODERATE
        elif complexity_score < 4.0:
            return Complexity.COMPLEX
        else:
            return Complexity.CRITICAL
    
    async def _determine_task_priority(self, description: str) -> Priority:
        """Determine task priority based on keywords"""
        description_lower = description.lower()
        
        priority_keywords = {
            Priority.CRITICAL: ['critical', 'urgent', 'emergency', 'production down', 'security breach'],
            Priority.HIGH: ['important', 'high priority', 'asap', 'blocking', 'deadline'],
            Priority.MEDIUM: ['normal', 'standard', 'regular', 'planned'],
            Priority.LOW: ['low priority', 'nice to have', 'future', 'enhancement', 'when time permits']
        }
        
        for priority, keywords in priority_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return priority
        
        return Priority.MEDIUM
    
    async def _identify_affected_files(self, description: str) -> List[str]:
        """Identify files that might be affected by the task"""
        affected_files = []
        
        # Look for explicit file mentions
        file_patterns = [
            r'([a-zA-Z_][a-zA-Z0-9_]*\.py)',  # Python files
            r'([a-zA-Z_][a-zA-Z0-9_]*\.js)',  # JavaScript files
            r'([a-zA-Z_][a-zA-Z0-9_]*\.ts)',  # TypeScript files
            r'([a-zA-Z_][a-zA-Z0-9_]*\.java)',  # Java files
            r'([a-zA-Z_][a-zA-Z0-9_]*\.[a-z]{2,4})',  # General files
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, description)
            affected_files.extend(matches)
        
        # Look for directory/module mentions
        if 'tests' in description.lower() or 'test' in description.lower():
            affected_files.extend(self._find_test_files())
        
        return list(set(affected_files))  # Remove duplicates
    
    def _find_test_files(self) -> List[str]:
        """Find test files in the project"""
        test_files = []
        test_patterns = ['**/test_*.py', '**/tests/*.py', '**/*_test.py', '**/*.test.js']
        
        for pattern in test_patterns:
            test_files.extend([str(f) for f in self.project_root.glob(pattern)])
        
        return test_files[:10]  # Limit to avoid too many results
    
    async def _estimate_effort(self, task_context: TaskContext) -> float:
        """Estimate effort in hours based on task context"""
        base_effort = {
            Complexity.TRIVIAL: 0.5,
            Complexity.SIMPLE: 2.0,
            Complexity.MODERATE: 8.0,
            Complexity.COMPLEX: 20.0,
            Complexity.CRITICAL: 40.0
        }
        
        effort = base_effort[task_context.complexity]
        
        # Adjust based on task type
        type_multipliers = {
            TaskType.BUG_FIX: 0.8,
            TaskType.REFACTORING: 1.2,
            TaskType.TESTING: 0.7,
            TaskType.DOCUMENTATION: 0.5,
            TaskType.SECURITY_FIX: 1.5,
            TaskType.INTEGRATION: 1.8,
            TaskType.DEPLOYMENT: 1.3
        }
        
        if task_context.task_type in type_multipliers:
            effort *= type_multipliers[task_context.task_type]
        
        return round(effort, 1)
    
    async def _assess_risk_level(self, task_context: TaskContext) -> str:
        """Assess risk level of the task"""
        risk_score = 0
        
        # Complexity contributes to risk
        complexity_risk = {
            Complexity.TRIVIAL: 1,
            Complexity.SIMPLE: 2,
            Complexity.MODERATE: 3,
            Complexity.COMPLEX: 4,
            Complexity.CRITICAL: 5
        }
        risk_score += complexity_risk[task_context.complexity]
        
        # Task type contributes to risk
        type_risk = {
            TaskType.SECURITY_FIX: 3,
            TaskType.DEPLOYMENT: 3,
            TaskType.REFACTORING: 2,
            TaskType.BUG_FIX: 1,
            TaskType.DOCUMENTATION: 0,
            TaskType.TESTING: 1
        }
        risk_score += type_risk.get(task_context.task_type, 2)
        
        # Priority contributes to risk
        priority_risk = {
            Priority.CRITICAL: 3,
            Priority.HIGH: 2,
            Priority.MEDIUM: 1,
            Priority.LOW: 0
        }
        risk_score += priority_risk[task_context.priority]
        
        # Map to risk level
        if risk_score <= 3:
            return "low"
        elif risk_score <= 6:
            return "medium"
        elif risk_score <= 9:
            return "high"
        else:
            return "critical"
    
    async def _suggest_approach(self, task_context: TaskContext) -> str:
        """Suggest an approach for completing the task"""
        approaches = {
            TaskType.BUG_FIX: "1. Reproduce the issue\n2. Identify root cause\n3. Implement minimal fix\n4. Add regression tests",
            TaskType.CODE_GENERATION: "1. Design the component interface\n2. Implement core functionality\n3. Add comprehensive tests\n4. Update documentation",
            TaskType.REFACTORING: "1. Ensure test coverage\n2. Refactor incrementally\n3. Run tests after each change\n4. Update documentation",
            TaskType.TESTING: "1. Identify test cases\n2. Write unit tests first\n3. Add integration tests\n4. Measure coverage",
            TaskType.SECURITY_FIX: "1. Assess vulnerability impact\n2. Implement secure solution\n3. Test security measures\n4. Document security implications"
        }
        
        return approaches.get(task_context.task_type, 
                            "1. Break down into smaller tasks\n2. Plan implementation steps\n3. Test incrementally\n4. Review and refine")
    
    async def suggest_workflows(self, task_context: TaskContext) -> List[WorkflowSuggestion]:
        """Suggest optimal workflows for the task"""
        
        suggestions = []
        
        # Get project context for better suggestions
        project_context = await self.analyze_project_context()
        
        # Select relevant workflow templates
        template_matches = {
            TaskType.BUG_FIX: ["bug_fix_standard"],
            TaskType.CODE_GENERATION: ["feature_development"],
            TaskType.REFACTORING: ["refactoring_safe"],
        }
        
        template_names = template_matches.get(task_context.task_type, ["feature_development"])
        
        for template_name in template_names:
            if template_name in self.workflow_templates:
                template = self.workflow_templates[template_name]
                
                # Customize template based on context
                customized = await self._customize_workflow(template, task_context, project_context)
                suggestions.append(customized)
        
        # Add AI-assisted workflow if complex enough
        if task_context.complexity in [Complexity.COMPLEX, Complexity.CRITICAL]:
            ai_workflow = await self._create_ai_assisted_workflow(task_context, project_context)
            suggestions.append(ai_workflow)
        
        # Sort by success probability and cost
        suggestions.sort(key=lambda x: (-x.success_probability, x.estimated_cost))
        
        return suggestions
    
    async def _customize_workflow(self, template: WorkflowSuggestion, 
                                task_context: TaskContext, 
                                project_context: ProjectContext) -> WorkflowSuggestion:
        """Customize workflow template based on context"""
        
        customized = WorkflowSuggestion(
            name=template.name,
            description=template.description,
            steps=template.steps[:],
            tools=template.tools[:],
            estimated_cost=template.estimated_cost,
            estimated_time_minutes=template.estimated_time_minutes,
            success_probability=template.success_probability,
            risk_factors=template.risk_factors[:]
        )
        
        # Adjust based on project languages
        if Language.PYTHON in project_context.languages:
            if "testing_framework" in customized.tools:
                customized.tools.append("pytest")
            
        # Adjust time based on complexity
        complexity_multipliers = {
            Complexity.TRIVIAL: 0.3,
            Complexity.SIMPLE: 0.7,
            Complexity.MODERATE: 1.0,
            Complexity.COMPLEX: 2.0,
            Complexity.CRITICAL: 4.0
        }
        
        multiplier = complexity_multipliers[task_context.complexity]
        customized.estimated_time_minutes = int(customized.estimated_time_minutes * multiplier)
        
        # Adjust success probability based on risk
        if task_context.risk_level == "high":
            customized.success_probability *= 0.8
        elif task_context.risk_level == "critical":
            customized.success_probability *= 0.6
        
        return customized
    
    async def _create_ai_assisted_workflow(self, task_context: TaskContext, 
                                         project_context: ProjectContext) -> WorkflowSuggestion:
        """Create AI-assisted workflow for complex tasks"""
        
        return WorkflowSuggestion(
            name="AI-Assisted Complex Task Workflow",
            description="AI-guided approach for complex development tasks",
            steps=[
                "AI analysis of task requirements and constraints",
                "Automated code generation and scaffolding",
                "AI-guided testing strategy development",
                "Iterative refinement with AI feedback",
                "Automated quality assurance checks",
                "AI-assisted documentation generation"
            ],
            tools=["claude_code", "copilot", "testing_ai", "doc_generator"],
            estimated_cost=2.50,
            estimated_time_minutes=int(task_context.estimated_effort_hours * 45),  # 45 min per hour with AI assistance
            success_probability=0.82,
            risk_factors=["AI hallucinations", "over-complexity", "cost overrun"]
        )
    
    def generate_context_report(self, task_description: str) -> Dict[str, Any]:
        """Generate a comprehensive context analysis report"""
        
        # This would be called asynchronously in practice
        # Simplified synchronous version for demonstration
        
        report = {
            "task_description": task_description,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "project_overview": {
                "root_path": str(self.project_root),
                "estimated_size": "medium",  # Would be calculated
                "primary_languages": ["python"],  # Would be detected
                "frameworks": []  # Would be detected
            },
            "task_analysis": {
                "type": "unknown",
                "complexity": "moderate", 
                "priority": "medium",
                "estimated_effort_hours": 4.0,
                "risk_level": "medium"
            },
            "recommendations": {
                "suggested_approach": "Standard development workflow",
                "tools": ["git", "testing_framework"],
                "estimated_cost": 0.50,
                "success_probability": 0.75
            }
        }
        
        return report


async def main():
    """Example usage of the Context Analysis Engine"""
    engine = ContextAnalysisEngine()
    
    # Analyze project context
    project_context = await engine.analyze_project_context()
    print(f"Project type: {project_context.project_type}")
    print(f"Languages: {project_context.languages}")
    print(f"Frameworks: {project_context.frameworks}")
    
    # Analyze a specific task
    task_context = await engine.analyze_task_context("Implement user authentication system with JWT tokens")
    print(f"Task type: {task_context.task_type}")
    print(f"Complexity: {task_context.complexity}")
    print(f"Estimated effort: {task_context.estimated_effort_hours} hours")
    
    # Get workflow suggestions
    workflows = await engine.suggest_workflows(task_context)
    print(f"Suggested workflows: {len(workflows)}")
    for workflow in workflows:
        print(f"  - {workflow.name}: {workflow.estimated_time_minutes} min, {workflow.success_probability:.2%} success")


if __name__ == "__main__":
    asyncio.run(main())