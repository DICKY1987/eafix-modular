# VS Code Workflow Integration Specification

## Overview
Technical specification for integrating all enterprise improvements into the existing VS Code development workflow, providing comprehensive control and monitoring capabilities.

## Current VS Code Configuration Status

### Existing Configuration
```
.vscode/
├── settings.json          # Python dev environment settings
├── tasks.json            # 22+ development tasks  
├── launch.json           # 12+ debug configurations
└── extensions.json       # 20+ recommended extensions
```

### Current Task Categories
- **CLI Multi-Rapid Platform Tasks** (7 tasks)
- **Development Tasks** (8 tasks)  
- **Legacy Agent Tasks** (3 tasks)
- **Git and Monitoring Tasks** (4 tasks)

## Enhanced VS Code Integration

### 1. New Task Categories

#### Enterprise Recovery Tasks
Add to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "inputs": [
    {
      "id": "recoveryRunbookId",
      "type": "pickString",
      "description": "Select recovery runbook",
      "options": [
        "database_connection_failure",
        "high_cpu_usage", 
        "memory_exhaustion",
        "service_failure",
        "position_limit_exceeded"
      ]
    },
    {
      "id": "serviceNameInput",
      "type": "promptString",
      "description": "Service name for recovery",
      "default": "api_server"
    }
  ],
  "tasks": [
    // Enterprise Recovery Management
    {
      "label": "Recovery: List Active Executions",
      "type": "shell",
      "command": "python -c \"from src.eafix.recovery.automated_recovery_system import AutomatedRecoverySystem; rs = AutomatedRecoverySystem(); print('Active Recoveries:', len(rs.active_executions)); [print(f'- {ex.id}: {ex.status.value}') for ex in rs.active_executions.values()]\"",
      "group": "build",
      "presentation": { "panel": "new", "showReuseMessage": false }
    },
    {
      "label": "Recovery: Show Statistics",
      "type": "shell", 
      "command": "python -c \"from src.eafix.recovery.automated_recovery_system import AutomatedRecoverySystem; rs = AutomatedRecoverySystem(); stats = rs.get_recovery_statistics(); print(f'Recovery Statistics:\\n- Total Runbooks: {stats[\\\"total_runbooks\\\"]}\\n- Total Executions: {stats[\\\"total_executions\\\"]}\\n- Success Rate: {stats[\\\"success_rate\\\"]:.2%}\\n- Active Executions: {stats[\\\"active_executions\\\"]}')\"",
      "group": "test",
      "presentation": { "panel": "new" }
    },
    {
      "label": "Recovery: Test Runbook",
      "type": "shell",
      "command": "python -c \"from src.eafix.recovery.automated_recovery_system import AutomatedRecoverySystem; import asyncio; rs = AutomatedRecoverySystem(); asyncio.run(rs.execute_recovery('test_${input:recoveryRunbookId}', {'error_message': 'Test execution', 'system': 'test', 'service_name': '${input:serviceNameInput}'}))\"",
      "group": "test",
      "presentation": { "panel": "new" }
    },
    {
      "label": "Recovery: Register New Runbook",
      "type": "shell",
      "command": "python scripts/register_recovery_runbook.py --interactive",
      "group": "build"
    }
  ]
}
```

#### Self-Healing Service Tasks
```json
{
  "tasks": [
    // Service Management
    {
      "label": "Services: Start Self-Healing Manager",
      "type": "shell",
      "command": "cd eafix-modular && docker-compose up -d service-manager",
      "group": "build",
      "presentation": { "panel": "new" }
    },
    {
      "label": "Services: Health Dashboard",
      "type": "shell", 
      "command": "cd eafix-modular && python -c \"import requests; import json; try: resp = requests.get('http://localhost:8090/services/status'); print(json.dumps(resp.json(), indent=2)); except: print('Service manager not running. Start with: Services: Start Self-Healing Manager')\"",
      "group": "test",
      "presentation": { "panel": "new", "showReuseMessage": false }
    },
    {
      "label": "Services: Restart All Services", 
      "type": "shell",
      "command": "cd eafix-modular && python -c \"import requests; resp = requests.post('http://localhost:8090/services/restart-all'); print(f'Restart initiated: {resp.status_code}')\"",
      "group": "build"
    },
    {
      "label": "Services: Scale Service",
      "type": "shell",
      "command": "cd eafix-modular && python scripts/scale_service.py --service ${input:serviceNameInput} --replicas ${input:replicaCount}",
      "group": "build"
    }
  ]
}
```

#### Predictive Monitoring Tasks
```json
{
  "tasks": [
    // Predictive Intelligence
    {
      "label": "Prediction: Train Models",
      "type": "shell",
      "command": "python -c \"from src.eafix.monitoring.predictive.predictive_failure_detector import PredictiveFailureDetector; import asyncio; detector = PredictiveFailureDetector(); asyncio.run(detector.train_models(force_retrain=True))\"",
      "group": "build",
      "presentation": { "panel": "new" }
    },
    {
      "label": "Prediction: Generate Forecasts", 
      "type": "shell",
      "command": "python -c \"from src.eafix.monitoring.predictive.predictive_failure_detector import PredictiveFailureDetector; import asyncio; detector = PredictiveFailureDetector(); predictions = asyncio.run(detector.predict_failures()); print(f'Generated {len(predictions)} predictions:'); [print(f'- {p.prediction_type.value}: {p.description} (confidence: {p.confidence:.2f})') for p in predictions[:5]]\"",
      "group": "test",
      "presentation": { "panel": "new", "showReuseMessage": false }
    },
    {
      "label": "Prediction: Show Prediction Summary",
      "type": "shell",
      "command": "python -c \"from src.eafix.monitoring.predictive.predictive_failure_detector import PredictiveFailureDetector; detector = PredictiveFailureDetector(); summary = detector.get_prediction_summary(); print(f'Prediction Summary:\\n- Total: {summary[\\\"total_predictions\\\"]}\\n- By Type: {summary[\\\"by_type\\\"]}\\n- By Severity: {summary[\\\"by_severity\\\"]}\\n- Critical Services: {summary[\\\"critical_services\\\"]}')\"",
      "group": "test"
    },
    {
      "label": "Prediction: Record Test Metrics",
      "type": "shell",
      "command": "python scripts/generate_test_metrics.py --days 7",
      "group": "build"
    }
  ]
}
```

#### Pipeline Orchestration Tasks  
```json
{
  "tasks": [
    // Deterministic Pipeline (from updatesfor_CLITOOL.json)
    {
      "label": "Pipeline: Start Orchestrator",
      "type": "shell",
      "command": "python orchestrator.py",
      "group": "build",
      "presentation": { "panel": "new" }
    },
    {
      "label": "Pipeline: Resume Orchestrator",
      "type": "shell", 
      "command": "python orchestrator.py --resume",
      "group": "build"
    },
    {
      "label": "Pipeline: Show Phase Status",
      "type": "shell",
      "command": "python -c \"import json; from pathlib import Path; state_file = Path('.ai/state.json'); print(json.dumps(json.loads(state_file.read_text()), indent=2) if state_file.exists() else 'No pipeline state found')\"",
      "group": "test",
      "presentation": { "panel": "new", "showReuseMessage": false }
    },
    {
      "label": "Pipeline: Validate Manifests",
      "type": "shell",
      "command": "python tools/validate_manifests.py",
      "group": "test"
    },
    {
      "label": "Pipeline: Run SAST Scan",
      "type": "shell",
      "command": "scripts/run_sast.sh",
      "group": "test"
    }
  ]
}
```

### 2. Enhanced Debug Configurations

Add to `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    // Enterprise Recovery Debugging
    {
      "name": "Debug: Recovery System",
      "type": "python",
      "request": "launch",
      "program": "src/eafix/recovery/automated_recovery_system.py",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      },
      "args": ["--test-mode"]
    },
    {
      "name": "Debug: Recovery Runbook Execution",
      "type": "python",
      "request": "launch", 
      "program": "scripts/test_recovery_runbook.py",
      "console": "integratedTerminal",
      "args": ["--runbook-id", "${input:recoveryRunbookId}"]
    },
    
    // Service Manager Debugging
    {
      "name": "Debug: Self-Healing Service Manager",
      "type": "python", 
      "request": "launch",
      "program": "eafix-modular/services/service-manager/src/main.py",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}/eafix-modular/services/service-manager"
    },
    {
      "name": "Debug: Service Health Checks",
      "type": "python",
      "request": "launch",
      "program": "eafix-modular/services/service-manager/src/health_checks.py", 
      "console": "integratedTerminal",
      "args": ["--service", "${input:serviceNameInput}"]
    },
    
    // Predictive System Debugging
    {
      "name": "Debug: Predictive Failure Detector",
      "type": "python",
      "request": "launch",
      "program": "src/eafix/monitoring/predictive/predictive_failure_detector.py",
      "console": "integratedTerminal", 
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      }
    },
    {
      "name": "Debug: Model Training",
      "type": "python",
      "request": "launch",
      "program": "scripts/train_prediction_models.py", 
      "console": "integratedTerminal",
      "args": ["--force-retrain", "--verbose"]
    },
    
    // Pipeline Orchestration Debugging
    {
      "name": "Debug: Pipeline Orchestrator",
      "type": "python",
      "request": "launch",
      "program": "orchestrator.py",
      "console": "integratedTerminal",
      "args": ["--debug", "--phase", "precheck"]
    },
    {
      "name": "Debug: Manifest Validation",
      "type": "python",
      "request": "launch", 
      "program": "tools/validate_manifests.py",
      "console": "integratedTerminal",
      "args": ["--verbose", "--fix"]
    }
  ]
}
```

### 3. Additional VS Code Inputs

Add to inputs section in `.vscode/tasks.json`:

```json
{
  "inputs": [
    {
      "id": "replicaCount", 
      "type": "promptString",
      "description": "Number of service replicas",
      "default": "2"
    },
    {
      "id": "predictionType",
      "type": "pickString",
      "description": "Select prediction type",
      "options": [
        "resource_exhaustion",
        "performance_degradation",
        "service_failure", 
        "memory_leak",
        "error_spike"
      ]
    },
    {
      "id": "pipelinePhase",
      "type": "pickString",
      "description": "Select pipeline phase",
      "options": [
        "precheck",
        "plan", 
        "critique",
        "generate",
        "validate",
        "mutate",
        "test",
        "gate",
        "docs_release",
        "cockpit",
        "done"
      ]
    }
  ]
}
```

### 4. Enterprise Settings Configuration

Add to `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
  
  // Enterprise Recovery Settings
  "files.associations": {
    "**/recovery_runbooks/*.json": "jsonc",
    "**/schemas/*.json": "jsonc",
    ".ai/*.json": "jsonc"
  },
  
  // Prediction Data Exclusions
  "files.exclude": {
    "**/prediction_data/models/**": true,
    "**/prediction_data/metrics.db": true,
    "**/.ai/state.json": false
  },
  
  // Task Auto-Discovery
  "typescript.preferences.includePackageJsonAutoImports": "auto",
  
  // Enterprise Debugging
  "python.debugging.console": "integratedTerminal",
  "python.testing.autoTestDiscoverOnSaveEnabled": true,
  
  // Pipeline State Monitoring  
  "files.watcherExclude": {
    "**/prediction_data/**": true,
    "**/recovery_runbooks/**": false,
    "**/.ai/**": false
  },
  
  // Enterprise Extension Settings
  "python.analysis.extraPaths": [
    "./src",
    "./eafix-modular/services",
    "./eafix-modular/shared"
  ],
  
  "python.testing.pytestArgs": [
    "tests/",
    "tests/integration/", 
    "eafix-modular/tests/"
  ]
}
```

### 5. Status Bar Integration

**File**: `vscode-extension/src/statusbar.ts` (create)

```typescript
import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

export class EnterpriseStatusBar {
    private recoveryStatusItem: vscode.StatusBarItem;
    private servicesStatusItem: vscode.StatusBarItem;
    private pipelineStatusItem: vscode.StatusBarItem;
    
    constructor() {
        // Recovery System Status
        this.recoveryStatusItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left, 100
        );
        this.recoveryStatusItem.command = 'enterprise.showRecoveryDashboard';
        
        // Services Status  
        this.servicesStatusItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left, 99
        );
        this.servicesStatusItem.command = 'enterprise.showServicesDashboard';
        
        // Pipeline Status
        this.pipelineStatusItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left, 98
        );
        this.pipelineStatusItem.command = 'enterprise.showPipelineStatus';
    }
    
    public updateRecoveryStatus() {
        // Read recovery statistics and update status bar
        try {
            const stats = this.getRecoveryStatistics();
            const activeRecoveries = stats.active_executions || 0;
            const successRate = ((stats.success_rate || 0) * 100).toFixed(0);
            
            if (activeRecoveries > 0) {
                this.recoveryStatusItem.text = `$(sync~spin) Recovery: ${activeRecoveries} active`;
                this.recoveryStatusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            } else {
                this.recoveryStatusItem.text = `$(check) Recovery: ${successRate}% success`;
                this.recoveryStatusItem.backgroundColor = undefined;
            }
        } catch (error) {
            this.recoveryStatusItem.text = "$(alert) Recovery: Error";
            this.recoveryStatusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
        }
        
        this.recoveryStatusItem.show();
    }
    
    public updateServicesStatus() {
        // Read service health and update status bar
        try {
            const health = this.getServicesHealth();
            const runningServices = health.running_services || 0;
            const totalServices = health.total_services || 0;
            const healthStatus = health.overall_health || 'unknown';
            
            const icon = healthStatus === 'healthy' ? '$(check)' : 
                        healthStatus === 'degraded' ? '$(warning)' : '$(error)';
                        
            this.servicesStatusItem.text = `${icon} Services: ${runningServices}/${totalServices}`;
            
            if (healthStatus !== 'healthy') {
                this.servicesStatusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            } else {
                this.servicesStatusItem.backgroundColor = undefined;
            }
        } catch (error) {
            this.servicesStatusItem.text = "$(alert) Services: Error";
            this.servicesStatusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
        }
        
        this.servicesStatusItem.show();
    }
    
    public updatePipelineStatus() {
        // Read pipeline state and update status bar
        try {
            const stateFile = path.join(vscode.workspace.rootPath || '', '.ai', 'state.json');
            if (fs.existsSync(stateFile)) {
                const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
                const currentPhase = state.current_phase || 'unknown';
                const status = state.status || 'idle';
                
                const icon = status === 'running' ? '$(sync~spin)' : 
                           status === 'completed' ? '$(check)' : 
                           status === 'failed' ? '$(error)' : '$(circle-outline)';
                           
                this.pipelineStatusItem.text = `${icon} Pipeline: ${currentPhase}`;
            } else {
                this.pipelineStatusItem.text = "$(circle-outline) Pipeline: Ready";
            }
        } catch (error) {
            this.pipelineStatusItem.text = "$(alert) Pipeline: Error";
        }
        
        this.pipelineStatusItem.show();
    }
    
    private getRecoveryStatistics(): any {
        // Execute Python script to get recovery statistics
        const { execSync } = require('child_process');
        const result = execSync('python -c "from src.eafix.recovery.automated_recovery_system import AutomatedRecoverySystem; rs = AutomatedRecoverySystem(); import json; print(json.dumps(rs.get_recovery_statistics()))"');
        return JSON.parse(result.toString());
    }
    
    private getServicesHealth(): any {
        // Execute request to service manager
        const { execSync } = require('child_process');
        const result = execSync('python -c "import requests, json; resp = requests.get(\'http://localhost:8090/health/summary\'); print(json.dumps(resp.json()))"');
        return JSON.parse(result.toString());
    }
    
    public dispose() {
        this.recoveryStatusItem.dispose();
        this.servicesStatusItem.dispose();
        this.pipelineStatusItem.dispose();
    }
}
```

### 6. Enterprise Command Palette Integration

**File**: `vscode-extension/src/commands.ts` (create)

```typescript
import * as vscode from 'vscode';

export class EnterpriseCommands {
    
    public static registerCommands(context: vscode.ExtensionContext) {
        
        // Recovery System Commands
        context.subscriptions.push(
            vscode.commands.registerCommand('enterprise.showRecoveryDashboard', () => {
                this.showRecoveryDashboard();
            })
        );
        
        context.subscriptions.push(
            vscode.commands.registerCommand('enterprise.executeRecoveryRunbook', () => {
                this.executeRecoveryRunbook();
            })
        );
        
        // Service Management Commands
        context.subscriptions.push(
            vscode.commands.registerCommand('enterprise.showServicesDashboard', () => {
                this.showServicesDashboard(); 
            })
        );
        
        context.subscriptions.push(
            vscode.commands.registerCommand('enterprise.restartService', () => {
                this.restartService();
            })
        );
        
        // Pipeline Commands
        context.subscriptions.push(
            vscode.commands.registerCommand('enterprise.showPipelineStatus', () => {
                this.showPipelineStatus();
            })
        );
        
        context.subscriptions.push(
            vscode.commands.registerCommand('enterprise.startPipeline', () => {
                this.startPipeline();
            })
        );
    }
    
    private static async showRecoveryDashboard() {
        const panel = vscode.window.createWebviewPanel(
            'recoveryDashboard',
            'Recovery Dashboard',
            vscode.ViewColumn.One,
            { enableScripts: true }
        );
        
        panel.webview.html = this.getRecoveryDashboardHtml();
    }
    
    private static async executeRecoveryRunbook() {
        const runbooks = ['database_connection_failure', 'high_cpu_usage', 'memory_exhaustion', 'service_failure'];
        
        const selected = await vscode.window.showQuickPick(runbooks, {
            placeHolder: 'Select recovery runbook to execute'
        });
        
        if (selected) {
            const terminal = vscode.window.createTerminal('Recovery Execution');
            terminal.sendText(`python -c "from src.eafix.recovery.automated_recovery_system import AutomatedRecoverySystem; import asyncio; rs = AutomatedRecoverySystem(); asyncio.run(rs.execute_recovery('test_${selected}', {'error_message': 'Manual execution', 'system': 'manual'}))" `);
            terminal.show();
        }
    }
    
    private static getRecoveryDashboardHtml(): string {
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Recovery Dashboard</title>
            <style>
                body { font-family: var(--vscode-font-family); }
                .metric { margin: 10px; padding: 10px; border: 1px solid var(--vscode-panel-border); }
                .success { color: var(--vscode-testing-iconPassed); }
                .error { color: var(--vscode-testing-iconFailed); }
                .warning { color: var(--vscode-testing-iconQueued); }
            </style>
        </head>
        <body>
            <h1>Enterprise Recovery Dashboard</h1>
            <div id="stats">Loading...</div>
            <script>
                // Load recovery statistics
                const vscode = acquireVsCodeApi();
                fetch('/recovery/stats')
                    .then(r => r.json())
                    .then(stats => {
                        document.getElementById('stats').innerHTML = \`
                            <div class="metric">
                                <h3>Active Recoveries</h3>
                                <span class="\${stats.active_executions > 0 ? 'warning' : 'success'}">\${stats.active_executions}</span>
                            </div>
                            <div class="metric">
                                <h3>Success Rate</h3>
                                <span class="\${stats.success_rate > 0.8 ? 'success' : 'warning'}">\${(stats.success_rate * 100).toFixed(1)}%</span>
                            </div>
                            <div class="metric">
                                <h3>Total Runbooks</h3>
                                <span>\${stats.total_runbooks}</span>
                            </div>
                        \`;
                    });
            </script>
        </body>
        </html>`;
    }
}
```

### 7. Workspace Configuration

**File**: `cli_multi_rapid_DEV.code-workspace` (create)

```json
{
    "folders": [
        {
            "name": "CLI Multi-Rapid (Root)",
            "path": "."
        },
        {
            "name": "Microservices",
            "path": "./eafix-modular"
        },
        {
            "name": "Recovery System",
            "path": "./src/eafix/recovery"
        },
        {
            "name": "Recovery Runbooks",
            "path": "./recovery_runbooks"
        },
        {
            "name": "Pipeline State",
            "path": "./.ai"
        }
    ],
    "settings": {
        "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
        "python.analysis.extraPaths": [
            "./src",
            "./eafix-modular/services",
            "./eafix-modular/shared"
        ],
        "files.associations": {
            "**/recovery_runbooks/*.json": "jsonc",
            "**/schemas/*.json": "jsonc",
            "**/.ai/*.json": "jsonc"
        }
    },
    "extensions": {
        "recommendations": [
            "ms-python.python",
            "ms-python.vscode-pylance", 
            "charliermarsh.ruff",
            "ms-vscode.vscode-json",
            "redhat.vscode-yaml",
            "eamodio.gitlens"
        ]
    },
    "tasks": {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "Enterprise: Full System Status",
                "type": "shell",
                "command": "python scripts/enterprise_status_check.py --comprehensive",
                "group": "test",
                "presentation": { "panel": "new" }
            }
        ]
    }
}
```

## Implementation Checklist

### Phase 1: Basic Integration
- [ ] Add recovery system tasks to `.vscode/tasks.json`
- [ ] Add service management tasks  
- [ ] Add predictive monitoring tasks
- [ ] Update debug configurations in `.vscode/launch.json`
- [ ] Test all new VS Code tasks work correctly

### Phase 2: Status Bar Integration  
- [ ] Create VS Code extension with status bar items
- [ ] Implement recovery status monitoring
- [ ] Implement services health monitoring  
- [ ] Implement pipeline status monitoring
- [ ] Test status updates work in real-time

### Phase 3: Dashboard Integration
- [ ] Create recovery dashboard webview
- [ ] Create services dashboard webview
- [ ] Create pipeline status webview  
- [ ] Add command palette integration
- [ ] Test all dashboards display correctly

### Phase 4: Workspace Configuration
- [ ] Create multi-folder workspace configuration
- [ ] Add folder-specific settings
- [ ] Configure extension recommendations
- [ ] Test workspace loads correctly with all folders

## Testing Commands

```bash
# Test VS Code tasks work correctly
code .
# Ctrl+Shift+P > "Tasks: Run Task" > "Recovery: Show Statistics"

# Test debug configurations  
# F5 > "Debug: Recovery System"

# Test status bar integration
# Verify status bar shows recovery/services/pipeline status

# Test command palette
# Ctrl+Shift+P > "Enterprise: Show Recovery Dashboard"
```

This comprehensive VS Code integration provides a unified development and operations interface for all enterprise improvements, making the CLI Multi-Rapid Enterprise Platform a complete, production-ready system with full IDE integration.