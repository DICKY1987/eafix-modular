Based on my analysis of the project documentation, here's what I've discovered about the GUI's current capabilities for tool visibility, progress tracking, and cost understanding:

## 🚨 **Current GUI Limitations - Major Gaps Identified**

### **❌ Tool Visibility & Progress Tracking**

**What's Missing:**
- **No real-time tool execution visibility** - Users cannot see which specific AI service (Claude, Gemini, Aider) is currently processing their task
- **No progress indicators** - No visual progress bars, spinners, or status updates during long-running operations
- **No workflow step visualization** - Users can't see the Research → Plan → Code workflow progression
- **No task queue visibility** - No way to see pending, running, or completed tasks
- **No tool selection rationale** - System doesn't explain WHY it chose a specific service

**Current State:**
```python
# User sees only basic terminal output like:
"🎯 Selected: gemini (Usage: 45/1000 (4.5%))"
# But no visual dashboard or progress tracking
```

### **❌ Cost Visibility & Management**

**What's Missing:**
- **No cost dashboard** - Despite cost being "a major constraint," there's no visual cost tracking interface
- **No real-time cost updates** - Users can't see costs accumulating during task execution
- **No budget alerts** - No warnings when approaching daily/monthly limits
- **No cost breakdown by tool** - Can't see spending per service (Claude vs Gemini vs local models)
- **No cost predictions** - No estimated cost before task execution

**Current State:**
```bash
# Only command-line cost monitoring available:
python .ai/scripts/cost-monitor.py
# Output: 💰 Estimated savings today: $1.95
# No GUI equivalent exists
```

## 🎯 **What the Current GUI Actually Provides**

### **Basic Terminal Interface**
- **Command execution** - Can run commands in PTY terminal
- **Signal handling** - Ctrl-C, EOF, Kill buttons work
- **Status strip** - Shows CWD, shell, dimensions, exit codes
- **Multi-tab support** - Multiple terminal sessions

### **Limited Monitoring**
- **Exit status** - Shows command success/failure
- **Execution time** - Basic duration tracking
- **Process management** - Can terminate running processes

### **No Enterprise Visibility**
The current GUI is essentially a **basic terminal emulator** with no enterprise workflow, cost, or tool orchestration visibility.

## 🚀 **Recommended GUI Enhancements for Tool & Cost Visibility**

### **1. Workflow Orchestration Dashboard**

```typescript
interface WorkflowDashboard {
  currentTask: {
    description: string;
    stage: 'analyzing' | 'researching' | 'planning' | 'coding' | 'reviewing';
    progress: number; // 0-100
    selectedTool: 'claude' | 'gemini' | 'aider' | 'ollama';
    selectionReason: string;
    estimatedCost: number;
  };
  
  taskQueue: TaskStatus[];
  completedTasks: TaskHistory[];
}
```

**Visual Elements:**
- **Progress ring** showing current task completion
- **Tool selection indicator** with reasoning tooltip
- **Stage pipeline** showing Research → Plan → Code progress
- **Queue visualization** for pending tasks

### **2. Real-Time Cost Tracking Dashboard**

```typescript
interface CostDashboard {
  today: {
    spent: number;
    budget: number;
    byService: { [service: string]: number };
    transactionHistory: CostTransaction[];
  };
  
  quotaStatus: {
    [service: string]: {
      used: number;
      limit: number;
      resetTime: Date;
    };
  };
  
  projections: {
    dailyTrend: number;
    monthlyEstimate: number;
    budgetBurnRate: 'healthy' | 'warning' | 'critical';
  };
}
```

**Visual Elements:**
- **Cost meter** with budget progress bar
- **Service quota gauges** for each AI service
- **Spending timeline** showing cost accumulation
- **Alert badges** for budget warnings

### **3. Tool Selection Intelligence Panel**

```typescript
interface ToolIntelligence {
  decisionMatrix: {
    taskComplexity: 'simple' | 'moderate' | 'complex';
    availableTools: ToolOption[];
    selectedTool: string;
    selectionFactors: {
      cost: number;
      capability: number;
      availability: number;
      performance: number;
    };
  };
  
  alternatives: {
    tool: string;
    reason: string;
    costDifference: number;
  }[];
}
```

**Visual Elements:**
- **Decision tree visualization** showing tool selection logic
- **Capability radar chart** comparing available tools
- **Cost comparison matrix** for alternatives
- **Override controls** for manual tool selection

## 📊 **Priority Implementation Roadmap**

### **Phase 1: Basic Visibility (1-2 weeks)**
```bash
# Add to current GUI:
1. Task status indicator in status bar
2. Simple progress spinner during operations
3. Cost counter updating in real-time
4. Tool selection display with tooltip explanation
```

### **Phase 2: Dashboard Integration (2-3 weeks)**
```typescript
// Add webview panels to existing GUI:
1. Workflow progress panel (left sidebar)
2. Cost tracking panel (bottom panel)
3. Tool comparison panel (right sidebar)
4. Task history panel (integrated with terminal)
```

### **Phase 3: Advanced Analytics (3-4 weeks)**
```python
# Add comprehensive monitoring:
1. Grafana dashboard integration
2. Cost trend analysis
3. Tool performance benchmarking
4. Predictive cost modeling
```

## 🚨 **Critical Missing Features Summary**

| Feature Category | Current State | User Impact | Implementation Priority |
|-----------------|---------------|-------------|------------------------|
| **Tool Visibility** | ❌ None | High - Users don't know what's happening | **Critical** |
| **Progress Tracking** | ❌ Basic terminal only | High - No workflow understanding | **Critical** |
| **Cost Dashboard** | ❌ CLI script only | Critical - Major constraint not visible | **Critical** |
| **Tool Selection Logic** | ❌ Hidden from user | Medium - No control/understanding | **High** |
| **Budget Alerts** | ❌ None | Critical - Risk of overspend | **Critical** |
| **Task Queue Management** | ❌ None | Medium - No workflow visibility | **Medium** |

## 💡 **Quick Win Implementation**

**Add to current `pty_terminal_runner.py`:**

```python
class EnhancedTerminalTab(TerminalTab):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add cost tracking widget
        self.cost_widget = CostTrackingWidget()
        
        # Add tool status widget  
        self.tool_widget = ToolStatusWidget()
        
        # Add progress indicator
        self.progress_widget = ProgressIndicatorWidget()
        
        # Wire up to existing layout
        self.status_layout.addWidget(self.cost_widget)
        self.status_layout.addWidget(self.tool_widget)
        self.status_layout.addWidget(self.progress_widget)
```

**Bottom Line:** The current GUI provides **zero visibility** into the sophisticated AI orchestration happening behind the scenes. Given that cost is "a major constraint," the lack of cost dashboard is a **critical missing feature** that should be the highest implementation priority.