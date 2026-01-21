# Panel System Architecture - Replication Guide

**Document Purpose**: Enable AI agents to replicate a modular panel-based UI system in new projects.

**Source System**: `ALL_AI/RUNTIME/gui/SUB_GUI`

**Date**: 2026-01-20

---

## Executive Summary

This document describes a **dual-interface panel system** architecture that provides both terminal-based (TUI) and windowed (GUI) interfaces for monitoring automation pipelines. The system uses a plugin-based panel registry pattern that allows dynamic registration and display of independent monitoring panels.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                 Application Layer                       │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │   TUI Interface  │      │   GUI Interface  │        │
│  │   (Textual)      │      │   (PySide6/Qt)   │        │
│  └────────┬─────────┘      └────────┬─────────┘        │
│           │                         │                  │
└───────────┼─────────────────────────┼──────────────────┘
            │                         │
            ↓                         ↓
┌─────────────────────────────────────────────────────────┐
│              Panel Registry System                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │  PanelRegistry (Central Registration)            │  │
│  │  - register(panel_id, panel_class)               │  │
│  │  - get(panel_id) → panel_class                   │  │
│  │  - create_panel(panel_id) → panel_instance       │  │
│  └──────────────────────────────────────────────────┘  │
└───────────┬─────────────────────────┬──────────────────┘
            │                         │
            ↓                         ↓
┌─────────────────────────────────────────────────────────┐
│                 Panel Plugins                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │Dashboard │  │File Life │  │Log Stream│  ...         │
│  │Panel     │  │Panel     │  │Panel     │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└───────────┬─────────────────────────┬──────────────────┘
            │                         │
            ↓                         ↓
┌─────────────────────────────────────────────────────────┐
│              Data Layer                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │State DB  │  │Event Log │  │Metrics   │              │
│  │(SQLite)  │  │(JSONL)   │  │Registry  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Panel Registry (Core System)

**Purpose**: Central registry for managing panel plugins with dynamic registration and instantiation.

**File**: `src/tui_app/core/panel_registry.py`

**Key Responsibilities**:
- Register panel classes with unique identifiers
- Retrieve panel classes by ID
- Create panel instances with context injection
- List available panels

**Implementation Pattern**:

```python
class PanelRegistry:
    """Registry for managing panel plugins."""
    
    def __init__(self):
        self._panels: Dict[str, Type[PanelPlugin]] = {}
    
    def register(self, panel_id: str, panel_class: Type[PanelPlugin]) -> None:
        """Register a panel plugin."""
        self._panels[panel_id] = panel_class
    
    def get(self, panel_id: str) -> Optional[Type[PanelPlugin]]:
        """Get panel class by ID."""
        return self._panels.get(panel_id)
    
    def list_panels(self) -> list[str]:
        """List all registered panel IDs."""
        return list(self._panels.keys())
    
    def create_panel(self, panel_id: str, context: PanelContext) -> Optional[PanelPlugin]:
        """Create a panel instance by ID with context."""
        panel_class = self.get(panel_id)
        if panel_class:
            return panel_class(context)
        return None
```

**Usage Pattern**:

```python
# Global registry instance
_panel_registry = PanelRegistry()

# Decorator for auto-registration
def register_panel(panel_id: str):
    def decorator(cls):
        _panel_registry.register(panel_id, cls)
        return cls
    return decorator

# In application code
@register_panel("dashboard")
class DashboardPanel:
    def __init__(self, context: PanelContext):
        self.context = context
```

---

### 2. Panel Plugin Protocol

**Purpose**: Define standard interface that all panels must implement.

**File**: `src/tui_app/core/panel_plugin.py`

**Required Interface**:

```python
class PanelPlugin(Protocol):
    """Protocol defining the panel plugin interface."""
    
    @property
    def panel_id(self) -> str:
        """Unique identifier for the panel."""
        ...
    
    @property
    def title(self) -> str:
        """Display title for the panel."""
        ...
    
    def create_widget(self) -> Widget:
        """Create the visual widget for this panel."""
        ...
    
    def refresh(self) -> None:
        """Refresh panel data (optional)."""
        ...
```

---

### 3. Panel Context

**Purpose**: Provide panels with access to shared resources (state clients, config, event bus).

**File**: `src/ui_core/panel_context.py`

**Structure**:

```python
@dataclass
class PanelContext:
    """Context data passed to panels."""
    
    config: UIConfig
    state_client: Optional[StateClient] = None
    pattern_client: Optional[PatternClient] = None
    event_bus: Optional[EventBus] = None
    run_id: Optional[str] = None
    
    def get_state_client(self) -> StateClient:
        """Get state client, raising if not configured."""
        if not self.state_client:
            raise RuntimeError("State client not configured")
        return self.state_client
```

**Usage**: Panels receive context at initialization and use it to query data:

```python
class DashboardPanel:
    def __init__(self, context: PanelContext):
        self.context = context
    
    def _refresh_data(self):
        # Query state through context
        summary = self.context.state_client.get_pipeline_summary()
        tasks = self.context.state_client.get_tasks(limit=5)
```

---

### 4. Concrete Panel Implementation Pattern

**Example**: Dashboard Panel (Pipeline Monitoring)

**File**: `src/tui_app/panels/dashboard_panel.py`

**Structure**:

```python
from textual.widgets import Static
from tui_app.core.panel_plugin import PanelContext
from tui_app.core.panel_registry import register_panel

class DashboardWidget(Static):
    """Dashboard widget with auto-refresh capability."""
    
    def __init__(self, context: PanelContext):
        super().__init__("", id="dashboard-content")
        self.context = context
        self.refresh_interval = 2.0  # seconds
    
    def on_mount(self) -> None:
        """Called when widget is mounted - start auto-refresh."""
        self._refresh_data()
        self.set_interval(self.refresh_interval, self._refresh_data)
    
    def _refresh_data(self) -> None:
        """Fetch and display updated dashboard data."""
        if not self.context.state_client:
            self.update("[bold red]No state client configured[/]")
            return
        
        # Get pipeline summary from state client
        summary = self.context.state_client.get_pipeline_summary()
        tasks = self.context.state_client.get_tasks(limit=5)
        
        # Build display text with Rich markup
        lines = [
            f"[bold cyan]Pipeline Status:[/] {summary.status.upper()}",
            f"Total Tasks:     {summary.total_tasks}",
            f"Running:         {summary.running_tasks}",
            f"Completed:       {summary.completed_tasks}",
            f"Failed:          {summary.failed_tasks}",
        ]
        
        self.update("\n".join(lines))

@register_panel("dashboard")
class DashboardPanel:
    """Main dashboard panel showing pipeline summary."""
    
    @property
    def panel_id(self) -> str:
        return "dashboard"
    
    @property
    def title(self) -> str:
        return "Pipeline Dashboard"
    
    def create_widget(self) -> DashboardWidget:
        return DashboardWidget(self.context)
```

---

## Panel Implementations Catalog

The source system includes 5 specialized panels:

### 1. **Dashboard Panel** (`dashboard`)
- **Purpose**: High-level pipeline status overview
- **Data Sources**: Pipeline state database (task counts, worker status)
- **Refresh Rate**: 2 seconds
- **Key Metrics**: Total/running/completed/failed tasks, active workers, recent task list

### 2. **File Lifecycle Panel** (`file_lifecycle`)
- **Purpose**: Track file changes through patch ledger
- **Data Sources**: Patch ledger database
- **Refresh Rate**: 3 seconds
- **Key Metrics**: Files created/modified/deleted, recent changes

### 3. **Log Stream Panel** (`log_stream`)
- **Purpose**: Live log viewing with filtering
- **Data Sources**: Log files or log aggregation service
- **Refresh Rate**: 1 second
- **Features**: Severity filtering, search, auto-scroll

### 4. **Pattern Activity Panel** (`pattern_activity`)
- **Purpose**: Monitor execution pattern usage
- **Data Sources**: Pattern execution database
- **Refresh Rate**: 2 seconds
- **Key Metrics**: Pattern invocation counts, success/failure rates

### 5. **Tool Health Panel** (`tool_health`)
- **Purpose**: Track tool errors and health status
- **Data Sources**: Tool error logs
- **Refresh Rate**: 5 seconds
- **Key Metrics**: Error counts by tool, recent errors

---

## TUI Implementation (Textual Framework)

**Framework**: [Textual](https://textual.textualize.io/) - Python TUI framework

**Main Application File**: `src/tui_app/main.py`

**Structure**:

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane

class PipelineMonitorApp(App):
    """Main TUI application with tabbed panel interface."""
    
    CSS = """
    /* Textual CSS for styling */
    Screen {
        background: $surface;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "switch_dashboard", "Dashboard"),
        ("f", "switch_file_lifecycle", "File Lifecycle"),
        ("l", "switch_log_stream", "Log Stream"),
    ]
    
    def __init__(self, context: PanelContext):
        super().__init__()
        self.context = context
        self.registry = get_panel_registry()
    
    def compose(self) -> ComposeResult:
        """Build the UI layout."""
        yield Header()
        
        with TabbedContent(initial="dashboard"):
            # Create tab for each registered panel
            for panel_id in self.registry.list_panels():
                panel = self.registry.create_panel(panel_id, self.context)
                with TabPane(panel.title, id=panel_id):
                    yield panel.create_widget()
        
        yield Footer()
    
    def action_switch_dashboard(self) -> None:
        """Switch to dashboard panel."""
        self.query_one(TabbedContent).active = "dashboard"
```

**Running TUI**:

```bash
# With mock data
python -m tui_app.main --use-mock-data

# With real backend
python -m tui_app.main --db-path /path/to/pipeline.db
```

---

## GUI Implementation (PySide6/Qt)

**Framework**: PySide6 (Qt for Python)

**Main Application File**: `src/gui_app_v2/main.py`

**Base Panel Widget** (`src/gui_app_v2/widgets/base_panel.py`):

```python
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

class BasePanelWidget(QWidget):
    """Base class for small panel widgets."""
    
    def __init__(self, title: str, refresh_interval: int = 2000, parent=None):
        super().__init__(parent)
        self.title = title
        self.refresh_interval = refresh_interval  # milliseconds
        self.setup_ui()
        self.start_refresh()
    
    def setup_ui(self):
        """Setup panel UI."""
        layout = QVBoxLayout(self)
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("font-weight: bold; color: #569cd6;")
        layout.addWidget(self.title_label)
        
        # Value display
        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.value_label)
        
        # Panel styling
        self.setStyleSheet("""
            BasePanelWidget {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
        """)
    
    def start_refresh(self):
        """Start auto-refresh timer."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(self.refresh_interval)
    
    def refresh_data(self):
        """Override in subclass to refresh data."""
        pass
    
    def set_value(self, value: str, color: str = "#d4d4d4"):
        """Set the main value display."""
        self.value_label.setText(str(value))
        self.value_label.setStyleSheet(f"font-size: 24px; color: {color};")
```

**Main Window with Tabbed Panels** (`src/gui_app_v2/core/main_window_v2.py`):

```python
from PySide6.QtWidgets import QMainWindow, QTabWidget

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, context: PanelContext):
        super().__init__()
        self.context = context
        self.setup_ui()
    
    def setup_ui(self):
        """Setup main window UI."""
        self.setWindowTitle("Pipeline Monitor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Register panels from registry
        registry = get_panel_registry()
        for panel_id in registry.list_panels():
            panel = registry.create_panel(panel_id, self.context)
            widget = panel.create_widget()
            self.tabs.addTab(widget, panel.title)
```

**Running GUI**:

```bash
# With mock data
python -m gui_app_v2.main --use-mock-data

# With real backend
python -m gui_app_v2.main --db-path /path/to/pipeline.db
```

---

## Data Backend Pattern

### State Client Interface

**Purpose**: Abstract data access layer for panels to query system state.

**File**: `src/ui_core/state_client.py`

**Interface**:

```python
class StateClient(ABC):
    """Abstract interface for querying system state."""
    
    @abstractmethod
    def get_pipeline_summary(self) -> PipelineSummary:
        """Get high-level pipeline status."""
        pass
    
    @abstractmethod
    def get_tasks(self, limit: int = 10) -> list[Task]:
        """Get recent tasks."""
        pass
    
    @abstractmethod
    def get_file_changes(self, limit: int = 10) -> list[FileChange]:
        """Get recent file changes."""
        pass
    
    @abstractmethod
    def get_pattern_activity(self) -> list[PatternExecution]:
        """Get pattern execution history."""
        pass
```

### Mock State Client (for development/testing)

```python
class MockStateClient(StateClient):
    """Mock implementation returning fake data."""
    
    def get_pipeline_summary(self) -> PipelineSummary:
        return PipelineSummary(
            status="running",
            total_tasks=42,
            running_tasks=3,
            completed_tasks=35,
            failed_tasks=4,
            active_workers=2
        )
    
    def get_tasks(self, limit: int = 10) -> list[Task]:
        return [
            Task(id="task-1", name="Process files", status="completed"),
            Task(id="task-2", name="Run validation", status="running"),
            Task(id="task-3", name="Generate report", status="pending"),
        ]
```

### SQLite State Client (for production)

```python
class SQLiteStateClient(StateClient):
    """SQLite-backed state client."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
    
    def get_pipeline_summary(self) -> PipelineSummary:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM tasks
        """)
        row = cursor.fetchone()
        return PipelineSummary(
            status="running",
            total_tasks=row[0],
            running_tasks=row[1],
            completed_tasks=row[2],
            failed_tasks=row[3],
            active_workers=self._get_active_workers()
        )
```

---

## Configuration System

**Config File**: `config/ui_config.yaml`

```yaml
gui:
  theme: "Fusion"  # Qt theme
  window:
    width: 1200
    height: 800
    title: "Pipeline Monitor"

tui:
  theme: "dark"

panels:
  dashboard: 2.0      # Refresh interval (seconds)
  file_lifecycle: 3.0
  tool_health: 5.0
  log_stream: 1.0
  pattern_activity: 2.0

backend:
  type: "sqlite"  # Options: sqlite, mock, http
  db_path: "../../pipeline.db"
  
logging:
  level: "INFO"
  file: "logs/ui.log"
```

**Loading Configuration**:

```python
import yaml
from dataclasses import dataclass

@dataclass
class UIConfig:
    """UI configuration."""
    panels: dict[str, float]
    backend_type: str
    db_path: str
    
    @classmethod
    def from_yaml(cls, path: str) -> 'UIConfig':
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(
            panels=data['panels'],
            backend_type=data['backend']['type'],
            db_path=data['backend']['db_path']
        )
```

---

## Replication Steps for New Project

### Step 1: Setup Project Structure

```
your_project/
├── src/
│   ├── ui_core/
│   │   ├── __init__.py
│   │   ├── panel_context.py      # PanelContext dataclass
│   │   ├── state_client.py       # StateClient interface
│   │   └── mock_state_client.py  # Mock implementation
│   ├── tui_app/
│   │   ├── __init__.py
│   │   ├── main.py               # TUI application entry point
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── panel_registry.py # PanelRegistry class
│   │   │   └── panel_plugin.py   # PanelPlugin protocol
│   │   └── panels/
│   │       ├── __init__.py
│   │       ├── dashboard_panel.py
│   │       └── ...other panels...
│   └── gui_app/
│       ├── __init__.py
│       ├── main.py               # GUI application entry point
│       ├── core/
│       │   ├── __init__.py
│       │   └── main_window.py
│       └── widgets/
│           ├── __init__.py
│           └── base_panel.py
├── config/
│   └── ui_config.yaml
└── requirements.txt
```

### Step 2: Install Dependencies

**requirements.txt**:
```
textual>=0.47.0        # For TUI
PySide6>=6.6.0         # For GUI
pyyaml>=6.0
```

### Step 3: Implement Core Components

1. **Panel Registry** (`src/tui_app/core/panel_registry.py`)
   - Copy the registry implementation from this guide
   - Add decorator for auto-registration

2. **Panel Context** (`src/ui_core/panel_context.py`)
   - Define dataclass with your required resources
   - Include config, state client, and any domain-specific services

3. **State Client Interface** (`src/ui_core/state_client.py`)
   - Define abstract methods for data queries your panels need
   - Create mock implementation first

4. **Panel Plugin Protocol** (`src/tui_app/core/panel_plugin.py`)
   - Define standard interface all panels must implement

### Step 4: Create First Panel

Start with a simple dashboard panel:

```python
# src/tui_app/panels/dashboard_panel.py

from textual.widgets import Static
from ..core.panel_registry import register_panel

class DashboardWidget(Static):
    def __init__(self, context):
        super().__init__()
        self.context = context
    
    def on_mount(self):
        self.set_interval(2.0, self._refresh)
    
    def _refresh(self):
        summary = self.context.state_client.get_summary()
        self.update(f"Status: {summary.status}\nTasks: {summary.total}")

@register_panel("dashboard")
class DashboardPanel:
    def __init__(self, context):
        self.context = context
    
    @property
    def panel_id(self) -> str:
        return "dashboard"
    
    @property
    def title(self) -> str:
        return "Dashboard"
    
    def create_widget(self):
        return DashboardWidget(self.context)
```

### Step 5: Build TUI Application

```python
# src/tui_app/main.py

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane
from ui_core.panel_context import PanelContext
from ui_core.mock_state_client import MockStateClient
from .core.panel_registry import get_panel_registry

class MonitorApp(App):
    def __init__(self):
        super().__init__()
        # Setup context
        self.context = PanelContext(
            config=load_config(),
            state_client=MockStateClient()
        )
        self.registry = get_panel_registry()
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with TabbedContent():
            for panel_id in self.registry.list_panels():
                panel = self.registry.create_panel(panel_id, self.context)
                with TabPane(panel.title, id=panel_id):
                    yield panel.create_widget()
        
        yield Footer()

if __name__ == "__main__":
    app = MonitorApp()
    app.run()
```

### Step 6: Build GUI Application (Optional)

If you need a windowed interface:

```python
# src/gui_app/main.py

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
from ui_core.panel_context import PanelContext
from ui_core.mock_state_client import MockStateClient

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitor")
        
        self.context = PanelContext(
            config=load_config(),
            state_client=MockStateClient()
        )
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Add panels
        registry = get_panel_registry()
        for panel_id in registry.list_panels():
            panel = registry.create_panel(panel_id, self.context)
            self.tabs.addTab(panel.create_widget(), panel.title)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

### Step 7: Add More Panels

For each new monitoring concern:

1. Create panel file in `src/tui_app/panels/`
2. Implement widget class with refresh logic
3. Implement panel class with `@register_panel` decorator
4. Add any new state client methods needed
5. Panel automatically appears in both TUI and GUI

---

## Testing Strategy

### Unit Tests for Panel Registry

```python
# tests/test_panel_registry.py

def test_register_panel():
    registry = PanelRegistry()
    
    class TestPanel:
        pass
    
    registry.register("test", TestPanel)
    assert registry.get("test") == TestPanel

def test_create_panel():
    registry = PanelRegistry()
    
    class TestPanel:
        def __init__(self, context):
            self.context = context
    
    registry.register("test", TestPanel)
    context = PanelContext(config=None)
    panel = registry.create_panel("test", context)
    
    assert isinstance(panel, TestPanel)
    assert panel.context == context
```

### Integration Tests for Panels

```python
# tests/test_dashboard_panel.py

def test_dashboard_panel_displays_summary():
    # Setup mock state client
    mock_client = MockStateClient()
    context = PanelContext(config=None, state_client=mock_client)
    
    # Create panel
    panel = DashboardPanel(context)
    widget = panel.create_widget()
    
    # Verify widget displays correct data
    assert "Status: running" in widget.render()
```

---

## Advanced Features

### Feature 1: Event-Driven Updates

Instead of polling, panels can subscribe to events:

```python
class EventBus:
    """Simple pub/sub event bus."""
    
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}
    
    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def publish(self, event_type: str, data: Any):
        for callback in self._subscribers.get(event_type, []):
            callback(data)

# In panel
class DashboardWidget(Static):
    def on_mount(self):
        self.context.event_bus.subscribe("task.completed", self._on_task_completed)
    
    def _on_task_completed(self, task):
        self._refresh_data()
```

### Feature 2: Panel Filtering/Search

```python
class LogStreamWidget(Static):
    def __init__(self, context):
        super().__init__()
        self.filter_level = "INFO"
    
    def compose(self):
        yield Input(placeholder="Filter logs...")
        yield Static(id="log-content")
    
    def on_input_changed(self, event):
        filter_text = event.value
        self._refresh_with_filter(filter_text)
```

### Feature 3: Panel State Persistence

```python
class PanelState:
    """Persist panel settings between sessions."""
    
    def save_panel_state(self, panel_id: str, state: dict):
        with open(f".panel_state_{panel_id}.json", "w") as f:
            json.dump(state, f)
    
    def load_panel_state(self, panel_id: str) -> dict:
        try:
            with open(f".panel_state_{panel_id}.json") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
```

---

## Performance Considerations

### 1. Refresh Rate Tuning

- **Fast panels** (< 1s): Logs, real-time metrics
- **Medium panels** (2-5s): Dashboard, task status
- **Slow panels** (5-10s): Aggregate analytics, health checks

### 2. Lazy Loading

```python
class ExpensivePanel:
    def __init__(self, context):
        self.context = context
        self._data_cache = None
    
    def _refresh_data(self):
        # Only fetch if panel is visible
        if self.is_visible:
            self._data_cache = self.context.state_client.get_expensive_data()
```

### 3. Data Pagination

```python
class TaskListPanel:
    def __init__(self, context):
        self.context = context
        self.page = 0
        self.page_size = 20
    
    def _fetch_tasks(self):
        offset = self.page * self.page_size
        return self.context.state_client.get_tasks(
            limit=self.page_size,
            offset=offset
        )
```

---

## Troubleshooting Guide

### Issue: Panel not appearing in tabs

**Solution**: Verify panel is registered with `@register_panel` decorator

### Issue: Panel shows "No state client configured"

**Solution**: Ensure `PanelContext` is initialized with state client:
```python
context = PanelContext(
    config=config,
    state_client=YourStateClient()  # Don't forget this!
)
```

### Issue: Refresh not working

**Solution**: Check refresh timer is started in `on_mount`:
```python
def on_mount(self):
    self.set_interval(self.refresh_interval, self._refresh_data)
```

### Issue: GUI not updating

**Solution**: Ensure Qt signals are used for cross-thread updates:
```python
from PySide6.QtCore import Signal

class PanelWidget(QWidget):
    data_ready = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.data_ready.connect(self._update_display)
```

---

## Reference Implementation Files

From source project `ALL_AI/RUNTIME/gui/SUB_GUI`:

### Core System Files
- `src/tui_app/core/panel_registry.py` - Panel registry implementation
- `src/tui_app/core/panel_plugin.py` - Plugin protocol definition
- `src/ui_core/panel_context.py` - Context dataclass

### Panel Implementations
- `src/tui_app/panels/dashboard_panel.py` - Pipeline dashboard
- `src/tui_app/panels/file_lifecycle_panel.py` - File change tracking
- `src/tui_app/panels/log_stream_panel.py` - Log viewer
- `src/tui_app/panels/pattern_activity_panel.py` - Pattern monitoring
- `src/tui_app/panels/tool_health_panel.py` - Tool health monitoring

### GUI Implementation
- `src/gui_app_v2/main.py` - GUI entry point
- `src/gui_app_v2/core/main_window_v2.py` - Main window
- `src/gui_app_v2/widgets/base_panel.py` - Base panel widget

### Documentation
- `DOC-GUIDE-AUTOMATION-GUI-ARCHITECTURE-295__AUTOMATION_GUI_ARCHITECTURE.md` - Architecture diagrams
- `DOC-GUIDE-GUI-FUNCTIONAL-STATUS-298__GUI_FUNCTIONAL_STATUS.md` - Operational status

---

## Summary Checklist for Replication

- [ ] Setup project structure with `ui_core/`, `tui_app/`, `gui_app/` directories
- [ ] Install dependencies (`textual`, `PySide6`, `pyyaml`)
- [ ] Implement `PanelRegistry` with registration system
- [ ] Define `PanelPlugin` protocol with required interface
- [ ] Create `PanelContext` dataclass with shared resources
- [ ] Implement `StateClient` interface (abstract + mock)
- [ ] Create first panel with auto-refresh capability
- [ ] Build TUI application with `Textual` framework
- [ ] (Optional) Build GUI application with `PySide6`
- [ ] Add configuration system with YAML
- [ ] Write unit tests for registry and panels
- [ ] Add launch scripts and documentation
- [ ] Implement production state client (SQLite/HTTP/etc.)
- [ ] Deploy and monitor

---

**End of Replication Guide**

This architecture provides a clean separation of concerns with:
- ✅ Pluggable panel system
- ✅ Dual interface support (TUI + GUI)
- ✅ Abstract data layer
- ✅ Auto-refresh capability
- ✅ Configuration-driven
- ✅ Testable components

The pattern is framework-agnostic at its core and can be adapted to any monitoring/dashboard use case.
