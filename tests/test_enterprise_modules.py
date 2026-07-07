#!/usr/bin/env python3
"""
Tests for Enterprise Modules (MOD-010 & Context Analysis Engine)
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Test the enterprise modules if available
try:
    from lib.automated_merge_strategy import (
        AutomatedMergeStrategy, 
        MergeStrategy, 
        ConflictComplexity, 
        MergeConflict
    )
    from lib.context_analysis_engine import (
        ContextAnalysisEngine,
        TaskType,
        Complexity,
        Priority,
        TaskContext,
        WorkflowSuggestion
    )
    ENTERPRISE_MODULES_AVAILABLE = True
except ImportError:
    ENTERPRISE_MODULES_AVAILABLE = False


@pytest.mark.skipif(not ENTERPRISE_MODULES_AVAILABLE, reason="Enterprise modules not available")
class TestAutomatedMergeStrategy:
    """Test MOD-010: Automated Merge Strategy"""
    
    @pytest.fixture
    def merge_strategy(self):
        """Create a test merge strategy instance"""
        return AutomatedMergeStrategy()
    
    def test_initialization(self, merge_strategy):
        """Test merge strategy initialization"""
        assert merge_strategy is not None
        assert hasattr(merge_strategy, 'merge_tools')
        assert hasattr(merge_strategy, 'strategy_rules')
        assert len(merge_strategy.merge_tools) > 0
    
    def test_merge_tool_configurations(self, merge_strategy):
        """Test merge tool configurations are valid"""
        for tool_name, tool_config in merge_strategy.merge_tools.items():
            assert tool_config.name == tool_name
            assert tool_config.cost_per_use >= 0.0
            assert len(tool_config.complexity_support) > 0
            assert tool_config.max_file_size > 0
            assert tool_config.timeout_seconds > 0
            assert 0.0 <= tool_config.success_rate <= 1.0
            assert callable(tool_config.availability_check)
    
    @pytest.mark.asyncio
    async def test_analyze_merge_conflicts_no_conflicts(self, merge_strategy):
        """Test merge conflict analysis with no conflicts"""
        # Mock git command to return no conflicts
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "merge successful"
            
            conflicts = await merge_strategy.analyze_merge_conflicts("main", "feature")
            assert isinstance(conflicts, list)
            assert len(conflicts) == 0
    
    @pytest.mark.asyncio 
    async def test_select_optimal_merge_tool_no_conflicts(self, merge_strategy):
        """Test tool selection with no conflicts"""
        conflicts = []  # No conflicts
        
        tool, strategy = await merge_strategy.select_optimal_merge_tool(conflicts)
        
        assert tool == "git_native"
        assert strategy == MergeStrategy.AUTO_MERGE
    
    @pytest.mark.asyncio
    async def test_select_optimal_merge_tool_with_conflicts(self, merge_strategy):
        """Test tool selection with conflicts"""
        # Create sample conflicts
        conflicts = [
            MergeConflict(
                file_path="test.py",
                conflict_type="content_conflict",
                complexity=ConflictComplexity.MODERATE,
                line_count=50,
                context_lines=[],
                base_content="",
                current_content="current version",
                incoming_content="incoming version"
            )
        ]
        
        tool, strategy = await merge_strategy.select_optimal_merge_tool(conflicts)
        
        assert tool is not None
        assert strategy is not None
        assert tool in merge_strategy.merge_tools
    
    def test_conflict_complexity_assessment(self, merge_strategy):
        """Test conflict complexity assessment"""
        # Simple conflict
        simple_complexity = merge_strategy._assess_conflict_complexity("simple text", "other text")
        assert isinstance(simple_complexity, ConflictComplexity)
        
        # Complex conflict with code patterns
        complex_content = """
        class MyClass:
            def __init__(self):
                import numpy as np
                @decorator
                def method(self):
                    pass
        """
        complex_complexity = merge_strategy._assess_conflict_complexity(complex_content, "other")
        assert complex_complexity in [ConflictComplexity.MODERATE, ConflictComplexity.COMPLEX, ConflictComplexity.CRITICAL]
    
    def test_availability_checks(self, merge_strategy):
        """Test tool availability checks"""
        # Test git availability (should work in most environments)
        git_available = merge_strategy._check_git_available()
        assert isinstance(git_available, bool)
        
        # Test manual editor (always available)
        manual_available = merge_strategy._check_vscode_available()
        assert isinstance(manual_available, bool)


@pytest.mark.skipif(not ENTERPRISE_MODULES_AVAILABLE, reason="Enterprise modules not available") 
class TestContextAnalysisEngine:
    """Test Context Analysis Engine"""
    
    @pytest.fixture
    def context_engine(self, tmp_path):
        """Create a test context engine instance"""
        return ContextAnalysisEngine(project_root=str(tmp_path))
    
    def test_initialization(self, context_engine):
        """Test context engine initialization"""
        assert context_engine is not None
        assert hasattr(context_engine, 'project_root')
        assert hasattr(context_engine, 'task_patterns')
        assert hasattr(context_engine, 'complexity_indicators')
        assert hasattr(context_engine, 'workflow_templates')
    
    def test_task_patterns_loaded(self, context_engine):
        """Test task patterns are properly loaded"""
        patterns = context_engine.task_patterns
        assert len(patterns) > 0
        
        # Check specific task types have patterns
        assert TaskType.BUG_FIX in patterns
        assert TaskType.CODE_GENERATION in patterns
        assert TaskType.REFACTORING in patterns
        
        for task_type, pattern_list in patterns.items():
            assert isinstance(pattern_list, list)
            assert len(pattern_list) > 0
    
    @pytest.mark.asyncio
    async def test_classify_task_type_bug_fix(self, context_engine):
        """Test task type classification for bug fixes"""
        bug_descriptions = [
            "fix the login bug",
            "resolve error in payment processing", 
            "debug the authentication issue"
        ]
        
        for desc in bug_descriptions:
            task_type = await context_engine._classify_task_type(desc)
            assert task_type == TaskType.BUG_FIX
    
    @pytest.mark.asyncio
    async def test_classify_task_type_feature(self, context_engine):
        """Test task type classification for features"""
        feature_descriptions = [
            "implement user registration",
            "create new API endpoint",
            "build shopping cart functionality"
        ]
        
        for desc in feature_descriptions:
            task_type = await context_engine._classify_task_type(desc)
            assert task_type == TaskType.CODE_GENERATION
    
    @pytest.mark.asyncio
    async def test_assess_task_complexity(self, context_engine):
        """Test task complexity assessment"""
        # Simple task
        simple_task = "fix typo in documentation"
        simple_complexity = await context_engine._assess_task_complexity(simple_task)
        assert simple_complexity in [Complexity.TRIVIAL, Complexity.SIMPLE]
        
        # Complex task with multiple indicators
        complex_task = "implement distributed microservices architecture with machine learning recommendations and real-time processing"
        complex_complexity = await context_engine._assess_task_complexity(complex_task)
        assert complex_complexity in [Complexity.COMPLEX, Complexity.CRITICAL]
    
    @pytest.mark.asyncio
    async def test_determine_task_priority(self, context_engine):
        """Test task priority determination"""
        # High priority task
        urgent_task = "critical security vulnerability fix needed immediately"
        urgent_priority = await context_engine._determine_task_priority(urgent_task)
        assert urgent_priority in [Priority.HIGH, Priority.URGENT, Priority.CRITICAL]
        
        # Low priority task
        low_task = "nice to have enhancement for future release"
        low_priority = await context_engine._determine_task_priority(low_task)
        assert low_priority == Priority.LOW
    
    @pytest.mark.asyncio
    async def test_analyze_task_context_full(self, context_engine):
        """Test full task context analysis"""
        task_desc = "implement JWT authentication for the API with proper error handling"
        
        task_context = await context_engine.analyze_task_context(task_desc)
        
        assert isinstance(task_context, TaskContext)
        assert task_context.description == task_desc
        assert task_context.task_type != TaskType.UNKNOWN
        assert task_context.complexity != Complexity.TRIVIAL  # Should be at least simple
        assert task_context.estimated_effort_hours > 0
        assert task_context.risk_level in ["low", "medium", "high", "critical"]
        assert len(task_context.suggested_approach) > 0
    
    @pytest.mark.asyncio
    async def test_identify_affected_files(self, context_engine):
        """Test affected files identification"""
        task_with_files = "update the user_model.py and authentication.js files"
        affected_files = await context_engine._identify_affected_files(task_with_files)
        
        assert isinstance(affected_files, list)
        # Should find at least the mentioned files
        assert any("user_model.py" in f or "authentication.js" in f for f in affected_files)
    
    def test_workflow_templates_loaded(self, context_engine):
        """Test workflow templates are properly loaded"""
        templates = context_engine.workflow_templates
        assert len(templates) > 0
        
        # Check for specific templates
        assert "bug_fix_standard" in templates
        assert "feature_development" in templates
        
        for template_name, template in templates.items():
            assert isinstance(template, WorkflowSuggestion)
            assert len(template.name) > 0
            assert len(template.steps) > 0
            assert template.estimated_time_minutes > 0
            assert 0.0 <= template.success_probability <= 1.0
    
    @pytest.mark.asyncio
    async def test_suggest_workflows(self, context_engine):
        """Test workflow suggestions"""
        # Create a sample task context
        task_context = TaskContext(
            description="fix authentication bug",
            task_type=TaskType.BUG_FIX,
            complexity=Complexity.MODERATE,
            priority=Priority.HIGH
        )
        
        workflows = await context_engine.suggest_workflows(task_context)
        
        assert isinstance(workflows, list)
        assert len(workflows) > 0
        
        for workflow in workflows:
            assert isinstance(workflow, WorkflowSuggestion)
            assert len(workflow.name) > 0
            assert len(workflow.steps) > 0
            assert workflow.estimated_cost >= 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_project_structure(self, context_engine, tmp_path):
        """Test project structure analysis"""
        # Create some test files
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "requirements.txt").write_text("flask==2.0.0\nrequests>=2.25.0")
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "app.py").write_text("from flask import Flask")
        
        # Re-create engine with the test directory
        test_engine = ContextAnalysisEngine(project_root=str(tmp_path))
        
        project_context = await test_engine.analyze_project_context()
        
        assert project_context.root_path == str(tmp_path)
        assert len(project_context.structure) > 0
        assert project_context.project_type != "unknown"  # Should detect as Python project
    
    def test_generate_context_report(self, context_engine):
        """Test context report generation"""
        task_desc = "implement user authentication"
        
        report = context_engine.generate_context_report(task_desc)
        
        assert isinstance(report, dict)
        assert "task_description" in report
        assert "analysis_timestamp" in report
        assert "project_overview" in report
        assert "task_analysis" in report
        assert "recommendations" in report
        
        assert report["task_description"] == task_desc


@pytest.mark.skipif(not ENTERPRISE_MODULES_AVAILABLE, reason="Enterprise modules not available")
class TestIntegration:
    """Test integration of enterprise modules with main framework"""
    
    def test_modules_can_be_imported(self):
        """Test that enterprise modules can be imported successfully"""
        assert ENTERPRISE_MODULES_AVAILABLE
        
        # Test basic instantiation
        merge_strategy = AutomatedMergeStrategy()
        context_engine = ContextAnalysisEngine()
        
        assert merge_strategy is not None
        assert context_engine is not None
    
    @pytest.mark.asyncio
    async def test_enterprise_module_workflow(self):
        """Test a basic enterprise module workflow"""
        # Initialize both modules
        merge_strategy = AutomatedMergeStrategy()
        context_engine = ContextAnalysisEngine()
        
        # Test context analysis
        task_desc = "implement merge conflict resolution"
        task_context = await context_engine.analyze_task_context(task_desc)
        
        assert task_context.task_type != TaskType.UNKNOWN
        assert task_context.complexity != Complexity.TRIVIAL
        
        # Test workflow suggestions
        workflows = await context_engine.suggest_workflows(task_context)
        assert len(workflows) > 0
        
        # Test merge strategy initialization
        assert len(merge_strategy.merge_tools) > 0
        assert len(merge_strategy.strategy_rules) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])