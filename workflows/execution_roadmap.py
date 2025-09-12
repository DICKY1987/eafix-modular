#!/usr/bin/env python3
"""
Execution Roadmap and Milestone Tracking System
Comprehensive tracking for the 13-phase implementation plan

This module provides milestone tracking, progress monitoring, and
automated validation for the complete implementation roadmap.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum
import yaml

try:
    from rich.console import Console
    from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeRemainingColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if RICH_AVAILABLE:
    console = Console()
else:
    console = None

class MilestoneStatus(str, Enum):
    """Milestone completion status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"

class PhaseCategory(str, Enum):
    """Phase categories for organization"""
    FOUNDATION = "foundation"
    ENHANCEMENT = "enhancement" 
    INTEGRATION = "integration"
    PRODUCTION = "production"
    VALIDATION = "validation"

@dataclass
class Milestone:
    """Individual milestone tracking"""
    id: str
    phase_id: str
    name: str
    description: str
    status: MilestoneStatus
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    dependencies: List[str] = None
    blockers: List[str] = None
    progress_percent: int = 0
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.blockers is None:
            self.blockers = []

@dataclass
class PhaseProgress:
    """Phase-level progress tracking"""
    phase_id: str
    name: str
    category: PhaseCategory
    status: MilestoneStatus
    start_date: Optional[datetime] = None
    target_end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    duration_days: int = 7
    progress_percent: int = 0
    milestones: List[Milestone] = None
    dependencies: List[str] = None
    risk_level: str = "medium"
    priority: str = "medium"
    
    def __post_init__(self):
        if self.milestones is None:
            self.milestones = []
        if self.dependencies is None:
            self.dependencies = []

@dataclass 
class ImplementationRoadmap:
    """Complete implementation roadmap tracking"""
    name: str
    start_date: datetime
    target_end_date: datetime
    phases: List[PhaseProgress]
    overall_progress: int = 0
    current_phase: Optional[str] = None
    completed_phases: int = 0
    blocked_phases: int = 0
    failed_phases: int = 0
    
    def calculate_overall_progress(self) -> int:
        """Calculate overall implementation progress"""
        if not self.phases:
            return 0
        
        total_progress = sum(phase.progress_percent for phase in self.phases)
        return total_progress // len(self.phases)

class RoadmapTracker:
    """
    Main tracking system for implementation roadmap
    
    Provides comprehensive tracking, validation, and reporting
    for the 13-phase implementation plan.
    """
    
    def __init__(self, roadmap_file: Optional[Path] = None):
        self.roadmap_file = roadmap_file or Path("workflows/roadmap_state.json")
        self.roadmap: Optional[ImplementationRoadmap] = None
        self.load_roadmap()
    
    def create_initial_roadmap(self) -> ImplementationRoadmap:
        """Create the initial 13-phase roadmap structure"""
        start_date = datetime.now()
        target_end_date = start_date + timedelta(days=90)
        
        # Define all 13 phases with their details
        phases = [
            # FOUNDATION PHASES (Days 1-21)
            PhaseProgress(
                phase_id="phase1",
                name="Core Workflow Activation",
                category=PhaseCategory.FOUNDATION,
                status=MilestoneStatus.NOT_STARTED,
                duration_days=7,
                risk_level="low",
                priority="critical",
                dependencies=[],
                milestones=[
                    Milestone("1.1", "phase1", "Execute Phase 0", "Project baseline and branch protection", MilestoneStatus.NOT_STARTED),
                    Milestone("1.2", "phase1", "Execute Phase 1", "Enhanced compliance and repository hygiene", MilestoneStatus.NOT_STARTED),
                    Milestone("1.3", "phase1", "Validate Compliance", "Ensure 85% coverage gates functional", MilestoneStatus.NOT_STARTED),
                    Milestone("1.4", "phase1", "Security Baseline", "Implement security scanning", MilestoneStatus.NOT_STARTED)
                ]
            ),
            PhaseProgress(
                phase_id="phase2",
                name="Template System Implementation",
                category=PhaseCategory.FOUNDATION,
                status=MilestoneStatus.NOT_STARTED,
                duration_days=7,
                risk_level="medium",
                priority="high",
                dependencies=["phase1"],
                milestones=[
                    Milestone("2.1", "phase2", "Create Template Engine", "Build template processing system", MilestoneStatus.NOT_STARTED),
                    Milestone("2.2", "phase2", "Implement Core Templates", "15+ executable templates", MilestoneStatus.NOT_STARTED),
                    Milestone("2.3", "phase2", "Template Validation", "Validation and syntax checking", MilestoneStatus.NOT_STARTED),
                    Milestone("2.4", "phase2", "Documentation", "Template usage documentation", MilestoneStatus.NOT_STARTED)
                ]
            ),
            PhaseProgress(
                phase_id="phase3", 
                name="Contract-Driven Development",
                category=PhaseCategory.FOUNDATION,
                status=MilestoneStatus.NOT_STARTED,
                duration_days=7,
                risk_level="high",
                priority="high",
                dependencies=["phase2"],
                milestones=[
                    Milestone("3.1", "phase3", "Schema Registry", "Centralized JSON schema registry", MilestoneStatus.NOT_STARTED),
                    Milestone("3.2", "phase3", "Model Generation", "Automated Pydantic model generation", MilestoneStatus.NOT_STARTED),
                    Milestone("3.3", "phase3", "Cross-Language Validation", "Python↔MQL4 consistency", MilestoneStatus.NOT_STARTED),
                    Milestone("3.4", "phase3", "Round-Trip Testing", "End-to-end validation", MilestoneStatus.NOT_STARTED)
                ]
            ),
            # ENHANCEMENT PHASES (Days 22-42)
            PhaseProgress(
                phase_id="phase4",
                name="Enhanced CLI Integration",
                category=PhaseCategory.ENHANCEMENT,
                status=MilestoneStatus.NOT_STARTED,
                duration_days=7,
                risk_level="low", 
                priority="medium",
                dependencies=["phase3"]
            ),
            PhaseProgress(
                phase_id="phase5",
                name="Production Monitoring System",
                category=PhaseCategory.ENHANCEMENT,
                status=MilestoneStatus.NOT_STARTED,
                duration_days=7,
                risk_level="medium",
                priority="high",
                dependencies=["phase4"]
            ),
            PhaseProgress(
                phase_id="phase6",
                name="Cross-Language Bridge",
                category=PhaseCategory.ENHANCEMENT,
                status=MilestoneStatus.NOT_STARTED,
                duration_days=7,
                risk_level="very_high",
                priority="high", 
                dependencies=["phase3", "phase5"]
            ),
            # INTEGRATION PHASES (Days 43-63)
            PhaseProgress(
                phase_id="phase7",
                name="Advanced Orchestration",
                category=PhaseCategory.INTEGRATION,
                status=MilestoneStatus.NOT_STARTED,
                duration_days=7,
                risk_level="medium",
                priority="medium",
                dependencies=["phase6"]
            ),
            PhaseProgress(
                phase_id="phase8", 
                name="Enterprise Security & Compliance",
                category=PhaseCategory.INTEGRATION,
                status=MilestoneStatus.NOT_STARTED,
                duration_days=7,
                risk_level="high",
                priority="high",
                dependencies=["phase7"]
            ),
            PhaseProgress(
                phase_id="phase9",
                name="AI-Enhanced Workflows",
                category=PhaseCategory.INTEGRATION,
                status=MilestoneStatus.NOT_STARTED,
                duration_days=7,
                risk_level="medium",
                priority="medium", 
                dependencies=["phase8"]
            ),
            # PRODUCTION PHASES (Days 64-84)
            PhaseProgress(
                phase_id="phase10",
                name="Multi-Environment Support", 
                category=PhaseCategory.PRODUCTION,
                status=MilestoneStatus.NOT_STARTED,
                duration_days=7,
                risk_level="medium",
                priority="high",
                dependencies=["phase9"]
            ),
            PhaseProgress(
                phase_id="phase11",
                name="Performance Optimization",
                category=PhaseCategory.PRODUCTION,
                status=MilestoneStatus.NOT_STARTED,
                duration_days=7,
                risk_level="low",
                priority="medium",
                dependencies=["phase10"]
            ),
            PhaseProgress(
                phase_id="phase12",
                name="Documentation & Training",
                category=PhaseCategory.PRODUCTION,
                status=MilestoneStatus.NOT_STARTED,
                duration_days=7,
                risk_level="low",
                priority="medium",
                dependencies=["phase11"]
            ),
            # VALIDATION PHASE (Days 85-90)
            PhaseProgress(
                phase_id="phase13",
                name="Final Validation & Launch",
                category=PhaseCategory.VALIDATION,
                status=MilestoneStatus.NOT_STARTED,
                duration_days=6,
                risk_level="low",
                priority="critical",
                dependencies=["phase12"]
            )
        ]
        
        # Calculate target dates for each phase
        current_date = start_date
        for phase in phases:
            phase.start_date = current_date
            phase.target_end_date = current_date + timedelta(days=phase.duration_days)
            current_date = phase.target_end_date + timedelta(days=1)  # 1 day buffer
        
        return ImplementationRoadmap(
            name="Enterprise Orchestration Platform Implementation",
            start_date=start_date,
            target_end_date=target_end_date,
            phases=phases,
            current_phase="phase1"
        )
    
    def load_roadmap(self) -> None:
        """Load roadmap state from file or create new one"""
        if self.roadmap_file.exists():
            try:
                with open(self.roadmap_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.roadmap = self.deserialize_roadmap(data)
                logger.info(f"Loaded existing roadmap from {self.roadmap_file}")
            except Exception as e:
                logger.warning(f"Failed to load roadmap: {e}, creating new one")
                self.roadmap = self.create_initial_roadmap()
        else:
            self.roadmap = self.create_initial_roadmap()
            self.save_roadmap()
            logger.info("Created new roadmap")
    
    def save_roadmap(self) -> None:
        """Save roadmap state to file"""
        if not self.roadmap:
            return
            
        try:
            # Ensure directory exists
            self.roadmap_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.roadmap_file, 'w', encoding='utf-8') as f:
                json.dump(self.serialize_roadmap(self.roadmap), f, indent=2)
            logger.info(f"Saved roadmap to {self.roadmap_file}")
        except Exception as e:
            logger.error(f"Failed to save roadmap: {e}")
    
    def serialize_roadmap(self, roadmap: ImplementationRoadmap) -> Dict[str, Any]:
        """Convert roadmap to JSON-serializable format"""
        def serialize_datetime(dt):
            return dt.isoformat() if dt else None
        
        serialized = asdict(roadmap)
        
        # Handle datetime serialization
        serialized['start_date'] = serialize_datetime(roadmap.start_date)
        serialized['target_end_date'] = serialize_datetime(roadmap.target_end_date)
        
        for phase_data in serialized['phases']:
            phase_data['start_date'] = serialize_datetime(phase_data['start_date'])
            phase_data['target_end_date'] = serialize_datetime(phase_data['target_end_date'])
            phase_data['actual_end_date'] = serialize_datetime(phase_data['actual_end_date'])
            
            for milestone_data in phase_data.get('milestones', []):
                milestone_data['start_date'] = serialize_datetime(milestone_data['start_date'])
                milestone_data['target_date'] = serialize_datetime(milestone_data['target_date'])
                milestone_data['completion_date'] = serialize_datetime(milestone_data['completion_date'])
        
        return serialized
    
    def deserialize_roadmap(self, data: Dict[str, Any]) -> ImplementationRoadmap:
        """Convert JSON data back to roadmap object"""
        def parse_datetime(dt_str):
            return datetime.fromisoformat(dt_str) if dt_str else None
        
        # Parse dates
        data['start_date'] = parse_datetime(data['start_date'])
        data['target_end_date'] = parse_datetime(data['target_end_date'])
        
        phases = []
        for phase_data in data['phases']:
            phase_data['start_date'] = parse_datetime(phase_data['start_date'])
            phase_data['target_end_date'] = parse_datetime(phase_data['target_end_date'])
            phase_data['actual_end_date'] = parse_datetime(phase_data['actual_end_date'])
            phase_data['category'] = PhaseCategory(phase_data['category'])
            phase_data['status'] = MilestoneStatus(phase_data['status'])
            
            milestones = []
            for milestone_data in phase_data.get('milestones', []):
                milestone_data['start_date'] = parse_datetime(milestone_data['start_date'])
                milestone_data['target_date'] = parse_datetime(milestone_data['target_date'])
                milestone_data['completion_date'] = parse_datetime(milestone_data['completion_date'])
                milestone_data['status'] = MilestoneStatus(milestone_data['status'])
                milestones.append(Milestone(**milestone_data))
            
            phase_data['milestones'] = milestones
            phases.append(PhaseProgress(**phase_data))
        
        data['phases'] = phases
        return ImplementationRoadmap(**data)
    
    def get_current_phase(self) -> Optional[PhaseProgress]:
        """Get the current active phase"""
        if not self.roadmap or not self.roadmap.current_phase:
            return None
        
        return next((p for p in self.roadmap.phases if p.phase_id == self.roadmap.current_phase), None)
    
    def get_next_phases(self) -> List[PhaseProgress]:
        """Get phases ready to be started (dependencies met)"""
        if not self.roadmap:
            return []
        
        completed_phases = {p.phase_id for p in self.roadmap.phases if p.status == MilestoneStatus.COMPLETED}
        
        ready_phases = []
        for phase in self.roadmap.phases:
            if (phase.status == MilestoneStatus.NOT_STARTED and 
                all(dep in completed_phases for dep in phase.dependencies)):
                ready_phases.append(phase)
        
        return ready_phases
    
    def update_phase_progress(self, phase_id: str, progress: int, status: Optional[MilestoneStatus] = None) -> None:
        """Update progress for a specific phase"""
        if not self.roadmap:
            return
        
        phase = next((p for p in self.roadmap.phases if p.phase_id == phase_id), None)
        if not phase:
            logger.warning(f"Phase {phase_id} not found")
            return
        
        phase.progress_percent = max(0, min(100, progress))
        
        if status:
            phase.status = status
            
            if status == MilestoneStatus.COMPLETED:
                phase.actual_end_date = datetime.now()
                if phase.phase_id == self.roadmap.current_phase:
                    # Move to next phase
                    next_phases = self.get_next_phases()
                    if next_phases:
                        self.roadmap.current_phase = next_phases[0].phase_id
        
        # Update overall progress
        self.roadmap.overall_progress = self.roadmap.calculate_overall_progress()
        self.save_roadmap()
    
    def display_roadmap_status(self) -> None:
        """Display comprehensive roadmap status"""
        if not self.roadmap:
            print("No roadmap loaded")
            return
        
        if console and RICH_AVAILABLE:
            self._display_rich_status()
        else:
            self._display_text_status()
    
    def _display_rich_status(self) -> None:
        """Display rich formatted status"""
        if not console or not self.roadmap:
            return
        
        # Overall progress panel
        overall_panel = Panel(
            f"Overall Progress: {self.roadmap.overall_progress}%\n"
            f"Current Phase: {self.roadmap.current_phase}\n"
            f"Start Date: {self.roadmap.start_date.strftime('%Y-%m-%d')}\n"
            f"Target End: {self.roadmap.target_end_date.strftime('%Y-%m-%d')}\n"
            f"Completed Phases: {self.roadmap.completed_phases}/{len(self.roadmap.phases)}",
            title="Implementation Roadmap Status",
            border_style="blue"
        )
        console.print(overall_panel)
        
        # Phases table
        table = Table(title="Phase Status Overview")
        table.add_column("Phase", style="cyan", width=20)
        table.add_column("Category", style="magenta") 
        table.add_column("Status", style="green")
        table.add_column("Progress", style="yellow")
        table.add_column("Start Date", style="blue")
        table.add_column("Target End", style="red")
        table.add_column("Risk", style="bright_yellow")
        
        for phase in self.roadmap.phases:
            status_color = {
                MilestoneStatus.NOT_STARTED: "white",
                MilestoneStatus.IN_PROGRESS: "yellow", 
                MilestoneStatus.COMPLETED: "green",
                MilestoneStatus.BLOCKED: "red",
                MilestoneStatus.FAILED: "red"
            }.get(phase.status, "white")
            
            table.add_row(
                phase.name,
                phase.category.value,
                f"[{status_color}]{phase.status.value}[/{status_color}]",
                f"{phase.progress_percent}%",
                phase.start_date.strftime('%m/%d') if phase.start_date else "TBD",
                phase.target_end_date.strftime('%m/%d') if phase.target_end_date else "TBD",
                phase.risk_level
            )
        
        console.print(table)
        
        # Dependencies tree for current phase
        current_phase = self.get_current_phase()
        if current_phase:
            tree = Tree(f"Current Phase: {current_phase.name}")
            for milestone in current_phase.milestones:
                status_icon = {
                    MilestoneStatus.NOT_STARTED: "[ ]",
                    MilestoneStatus.IN_PROGRESS: "[~]",
                    MilestoneStatus.COMPLETED: "[X]",
                    MilestoneStatus.BLOCKED: "[!]",
                    MilestoneStatus.FAILED: "[E]"
                }.get(milestone.status, "[ ]")
                
                tree.add(f"{status_icon} {milestone.name} ({milestone.progress_percent}%)")
            
            console.print(Panel(tree, title="Current Phase Details"))
    
    def _display_text_status(self) -> None:
        """Display text-based status for systems without rich"""
        if not self.roadmap:
            return
        
        print("\n" + "="*60)
        print("IMPLEMENTATION ROADMAP STATUS")
        print("="*60)
        print(f"Overall Progress: {self.roadmap.overall_progress}%")
        print(f"Current Phase: {self.roadmap.current_phase}")
        print(f"Completed: {self.roadmap.completed_phases}/{len(self.roadmap.phases)} phases")
        
        print("\nPHASE BREAKDOWN:")
        for phase in self.roadmap.phases:
            status_icon = {
                MilestoneStatus.NOT_STARTED: "[ ]",
                MilestoneStatus.IN_PROGRESS: "[~]", 
                MilestoneStatus.COMPLETED: "[X]",
                MilestoneStatus.BLOCKED: "[!]",
                MilestoneStatus.FAILED: "[E]"
            }.get(phase.status, "[ ]")
            
            print(f"{status_icon} {phase.phase_id}: {phase.name} ({phase.progress_percent}%)")
    
    async def execute_roadmap(self, start_from: Optional[str] = None) -> None:
        """Execute the complete roadmap starting from specified phase"""
        if not self.roadmap:
            logger.error("No roadmap loaded")
            return
        
        if start_from:
            self.roadmap.current_phase = start_from
        
        console.print("[bold green]Starting roadmap execution...[/bold green]") if console else print("Starting roadmap execution...")
        
        # This would integrate with the workflow orchestrator
        # For now, just demonstrate the tracking capability
        current_phase = self.get_current_phase()
        if current_phase:
            console.print(f"[blue]Would execute phase: {current_phase.name}[/blue]") if console else print(f"Would execute phase: {current_phase.name}")

# CLI Interface
async def main():
    """Main CLI interface for roadmap tracking"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Implementation Roadmap Tracker")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show roadmap status")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update phase progress")
    update_parser.add_argument("phase_id", help="Phase ID to update")
    update_parser.add_argument("progress", type=int, help="Progress percentage (0-100)")
    update_parser.add_argument("--status", choices=[s.value for s in MilestoneStatus], help="Phase status")
    
    # Execute command
    execute_parser = subparsers.add_parser("execute", help="Execute roadmap")
    execute_parser.add_argument("--start-from", help="Phase to start from")
    
    args = parser.parse_args()
    
    tracker = RoadmapTracker()
    
    if args.command == "status":
        tracker.display_roadmap_status()
        return 0
        
    elif args.command == "update":
        status = MilestoneStatus(args.status) if args.status else None
        tracker.update_phase_progress(args.phase_id, args.progress, status)
        if console:
            console.print(f"[green]Updated {args.phase_id} to {args.progress}%[/green]")
        else:
            print(f"Updated {args.phase_id} to {args.progress}%")
        return 0
        
    elif args.command == "execute":
        await tracker.execute_roadmap(args.start_from)
        return 0
    
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    asyncio.run(main())