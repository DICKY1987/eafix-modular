# Guardian System Integration Specification

## Overview
Technical specification for integrating the Automated Recovery System with the existing Guardian multi-agent protection system.

## Current Guardian Architecture

### Existing Components
```
src/eafix/guardian/
├── agents/
│   ├── risk_agent.py           # Risk monitoring and analysis
│   ├── market_agent.py         # Market condition monitoring  
│   ├── system_agent.py         # System health monitoring
│   ├── compliance_agent.py     # Compliance validation
│   ├── execution_agent.py      # Trade execution monitoring
│   └── learning_agent.py       # Pattern learning and optimization
├── constraints/
│   ├── constraint_repository.py  # Constraint management
│   ├── constraint_dsl.py         # Domain-specific language for constraints
│   └── constraint_engine.py      # Constraint evaluation engine
└── gates/
    ├── broker_gate.py          # Broker connectivity validation
    ├── market_quality_gate.py  # Market data quality checks
    ├── risk_gate.py           # Risk management gates
    └── system_health_gate.py  # System health validation
```

### Current Alert Flow
1. Agent detects issue → 2. Logs alert → 3. Updates monitoring tiles → 4. **Manual intervention required**

### Target Recovery Flow  
1. Agent detects issue → 2. Triggers automated recovery → 3. Executes remediation → 4. Verifies success → 5. Updates status

## Integration Points

### 1. Agent Enhancement

**File**: `src/eafix/guardian/agents/base_agent.py` (create if not exists)

```python
from abc import ABC, abstractmethod
from eafix.recovery.automated_recovery_system import AutomatedRecoverySystem
import asyncio

class BaseGuardianAgent(ABC):
    """Base class for all Guardian agents with recovery integration."""
    
    def __init__(self):
        self.recovery_system = AutomatedRecoverySystem()
        self.agent_id = self.__class__.__name__.lower()
        
    async def handle_issue(self, issue_data: dict) -> dict:
        """Enhanced issue handling with automatic recovery."""
        # Log the issue (existing behavior)
        self.log_issue(issue_data)
        
        # Try automated recovery (new behavior)
        if self.should_attempt_recovery(issue_data):
            recovery_id = await self.execute_recovery(issue_data)
            issue_data['recovery_execution_id'] = recovery_id
            
        return issue_data
    
    async def execute_recovery(self, issue_data: dict) -> str:
        """Execute automated recovery for the issue."""
        recovery_data = self.map_issue_to_recovery_data(issue_data)
        return await self.recovery_system.execute_recovery(
            error_id=f"{self.agent_id}_{issue_data.get('id', 'unknown')}",
            error_data=recovery_data
        )
    
    @abstractmethod
    def map_issue_to_recovery_data(self, issue_data: dict) -> dict:
        """Map agent-specific issue data to recovery system format."""
        pass
        
    def should_attempt_recovery(self, issue_data: dict) -> bool:
        """Determine if automated recovery should be attempted."""
        severity = issue_data.get('severity', 'low')
        return severity in ['medium', 'high', 'critical']
```

### 2. Risk Agent Integration

**File**: `src/eafix/guardian/agents/risk_agent.py` (modify existing)

```python
from .base_agent import BaseGuardianAgent

class RiskAgent(BaseGuardianAgent):
    """Risk monitoring with automated recovery capabilities."""
    
    def map_issue_to_recovery_data(self, issue_data: dict) -> dict:
        """Map risk issues to recovery format."""
        risk_type = issue_data.get('risk_type', 'unknown')
        
        recovery_mapping = {
            'position_limit_exceeded': {
                'error_message': f"Position limit exceeded: {issue_data.get('details', '')}",
                'system': 'risk_management',
                'service_name': 'position_manager',
                'risk_type': risk_type,
                'current_exposure': issue_data.get('current_exposure'),
                'limit_threshold': issue_data.get('limit_threshold')
            },
            'margin_call': {
                'error_message': f"Margin call triggered: {issue_data.get('details', '')}",
                'system': 'risk_management', 
                'service_name': 'margin_monitor',
                'account_balance': issue_data.get('account_balance'),
                'required_margin': issue_data.get('required_margin')
            },
            'drawdown_exceeded': {
                'error_message': f"Maximum drawdown exceeded: {issue_data.get('details', '')}",
                'system': 'risk_management',
                'service_name': 'drawdown_monitor',
                'current_drawdown': issue_data.get('current_drawdown'),
                'max_drawdown': issue_data.get('max_drawdown')
            }
        }
        
        return recovery_mapping.get(risk_type, {
            'error_message': f"Unknown risk issue: {risk_type}",
            'system': 'risk_management',
            'service_name': 'risk_agent'
        })
```

### 3. System Agent Integration  

**File**: `src/eafix/guardian/agents/system_agent.py` (modify existing)

```python
from .base_agent import BaseGuardianAgent

class SystemAgent(BaseGuardianAgent):
    """System health monitoring with automated recovery."""
    
    def map_issue_to_recovery_data(self, issue_data: dict) -> dict:
        """Map system issues to recovery format."""
        system_issue = issue_data.get('system_issue_type', 'unknown')
        
        recovery_mapping = {
            'high_cpu_usage': {
                'error_message': f"High CPU usage detected: {issue_data.get('cpu_usage', 0)}%",
                'system': 'system_resources',
                'service_name': issue_data.get('service_name', 'system'),
                'cpu_usage': issue_data.get('cpu_usage'),
                'threshold': issue_data.get('cpu_threshold', 80)
            },
            'memory_exhaustion': {
                'error_message': f"Memory usage critical: {issue_data.get('memory_usage', 0)}%", 
                'system': 'system_resources',
                'service_name': issue_data.get('service_name', 'system'),
                'memory_usage': issue_data.get('memory_usage'),
                'threshold': issue_data.get('memory_threshold', 85)
            },
            'disk_space_low': {
                'error_message': f"Disk space low: {issue_data.get('free_space', 0)}MB remaining",
                'system': 'system_resources', 
                'service_name': 'disk_monitor',
                'free_space_mb': issue_data.get('free_space'),
                'threshold_mb': issue_data.get('disk_threshold', 1000)
            },
            'service_down': {
                'error_message': f"Service unavailable: {issue_data.get('service_name', 'unknown')}",
                'system': 'service_management',
                'service_name': issue_data.get('service_name', 'unknown'),
                'last_response': issue_data.get('last_response_time'),
                'health_check_url': issue_data.get('health_check_url')
            }
        }
        
        return recovery_mapping.get(system_issue, {
            'error_message': f"Unknown system issue: {system_issue}",
            'system': 'system_management',
            'service_name': 'system_agent'
        })
```

### 4. Recovery Runbook Specifications

**Directory**: `recovery_runbooks/guardian/`

#### Risk Management Runbooks

**File**: `recovery_runbooks/guardian/position_limit_exceeded.json`
```json
{
  "id": "position_limit_exceeded",
  "name": "Position Limit Recovery",
  "description": "Automatically reduce position size when limits are exceeded",
  "error_patterns": ["position.*limit.*exceeded", "exposure.*too.*high"],
  "error_conditions": {"system": "risk_management", "risk_type": "position_limit_exceeded"},
  "actions": [
    {
      "id": "calculate_reduction",
      "name": "Calculate Required Position Reduction",
      "action_type": "custom_function",
      "parameters": {
        "function_name": "calculate_position_reduction"
      },
      "risk_level": "medium"
    },
    {
      "id": "reduce_positions",
      "name": "Reduce Positions",
      "action_type": "api_call",
      "parameters": {
        "url": "http://localhost:8080/positions/reduce",
        "method": "POST",
        "json": {
          "reduction_percentage": "{calculated_reduction}",
          "reason": "automated_risk_management"
        }
      },
      "risk_level": "high",
      "requires_confirmation": true,
      "dependencies": ["calculate_reduction"]
    }
  ],
  "auto_execute": true,
  "requires_approval": true,
  "success_criteria": ["curl -s http://localhost:8080/positions/status | jq '.total_exposure < .limit'"]
}
```

**File**: `recovery_runbooks/guardian/high_cpu_usage.json`
```json
{
  "id": "high_cpu_usage",
  "name": "High CPU Usage Recovery",
  "description": "Reduce system load when CPU usage is critical",
  "error_patterns": ["cpu.*usage.*high", "cpu.*exceeded.*threshold"],
  "error_conditions": {"system": "system_resources", "system_issue_type": "high_cpu_usage"},
  "actions": [
    {
      "id": "identify_high_cpu_processes",
      "name": "Identify High CPU Processes",
      "action_type": "command",
      "command": "ps aux --sort=-%cpu | head -10",
      "risk_level": "low"
    },
    {
      "id": "restart_high_cpu_service",
      "name": "Restart High CPU Service",
      "action_type": "service_restart",
      "parameters": {
        "service_name": "{service_name}"
      },
      "risk_level": "medium",
      "dependencies": ["identify_high_cpu_processes"]
    },
    {
      "id": "enable_cpu_throttling",
      "name": "Enable CPU Throttling",
      "action_type": "configuration_change",
      "parameters": {
        "file_path": "/etc/systemd/system/{service_name}.service",
        "changes": {
          "CPUQuota": "80%"
        }
      },
      "risk_level": "low"
    }
  ],
  "auto_execute": true,
  "success_criteria": ["test $(cat /proc/loadavg | cut -d' ' -f1 | cut -d'.' -f1) -lt 4"]
}
```

### 5. Constraint Repository Integration

**File**: `src/eafix/guardian/constraints/constraint_repository.py` (modify existing)

```python
class ConstraintRepository:
    """Enhanced constraint repository with recovery integration."""
    
    def __init__(self):
        # Existing initialization
        self.recovery_system = AutomatedRecoverySystem()
        self.constraint_recovery_mapping = self._initialize_constraint_recovery_mapping()
    
    def _initialize_constraint_recovery_mapping(self) -> dict:
        """Map constraint types to recovery runbook IDs."""
        return {
            'position_limit': 'position_limit_exceeded',
            'margin_requirement': 'margin_call_recovery',
            'drawdown_limit': 'drawdown_exceeded_recovery',
            'cpu_usage_limit': 'high_cpu_usage',
            'memory_usage_limit': 'memory_exhaustion',
            'disk_space_limit': 'disk_space_low',
            'service_availability': 'service_down'
        }
    
    async def handle_constraint_violation(self, constraint: dict, violation_data: dict) -> dict:
        """Handle constraint violation with automatic recovery."""
        # Existing violation handling
        violation_result = self._process_violation(constraint, violation_data)
        
        # Attempt automated recovery
        constraint_type = constraint.get('type')
        if constraint_type in self.constraint_recovery_mapping:
            recovery_data = self._map_constraint_to_recovery_data(
                constraint, violation_data
            )
            
            execution_id = await self.recovery_system.execute_recovery(
                error_id=f"constraint_{constraint['id']}",
                error_data=recovery_data
            )
            
            violation_result['recovery_execution_id'] = execution_id
            
        return violation_result
    
    def _map_constraint_to_recovery_data(self, constraint: dict, violation_data: dict) -> dict:
        """Map constraint violation to recovery system format."""
        return {
            'error_message': f"Constraint violation: {constraint['name']}",
            'system': 'constraint_management',
            'constraint_id': constraint['id'],
            'constraint_type': constraint['type'],
            'violation_value': violation_data.get('current_value'),
            'constraint_limit': constraint.get('limit'),
            'service_name': violation_data.get('service_name', 'constraint_monitor')
        }
```

### 6. Enhanced Monitoring Tiles Integration

**File**: `src/eafix/gui/enhanced/monitoring_tiles.py` (modify existing)

```python
class MonitoringTiles:
    """Enhanced monitoring tiles showing recovery status."""
    
    def __init__(self):
        # Existing initialization
        self.recovery_system = AutomatedRecoverySystem()
    
    def create_recovery_status_tile(self) -> tk.Frame:
        """Create tile showing active recoveries."""
        tile = tk.Frame(self.master, **self.tile_style)
        
        # Title
        title_label = tk.Label(tile, text="Recovery Status", **self.title_style)
        title_label.pack()
        
        # Active recoveries count
        stats = self.recovery_system.get_recovery_statistics()
        active_recoveries = stats.get('active_executions', 0)
        
        active_label = tk.Label(
            tile, 
            text=f"Active: {active_recoveries}",
            **self.value_style
        )
        active_label.pack()
        
        # Success rate
        success_rate = stats.get('success_rate', 0) * 100
        success_label = tk.Label(
            tile,
            text=f"Success: {success_rate:.1f}%",
            **self.value_style
        )
        success_label.pack()
        
        # Recent executions button
        recent_button = tk.Button(
            tile,
            text="View Recent",
            command=self.show_recent_recoveries
        )
        recent_button.pack()
        
        return tile
    
    def show_recent_recoveries(self):
        """Show popup with recent recovery executions."""
        popup = tk.Toplevel(self.master)
        popup.title("Recent Recovery Executions")
        popup.geometry("600x400")
        
        # Get recent executions
        recent_executions = self.recovery_system.execution_history[-10:]
        
        # Create treeview with execution details
        tree = ttk.Treeview(popup, columns=('id', 'status', 'success_rate', 'start_time'))
        tree.heading('#0', text='Runbook')
        tree.heading('id', text='Execution ID')
        tree.heading('status', text='Status')
        tree.heading('success_rate', text='Success Rate')
        tree.heading('start_time', text='Start Time')
        
        for execution in recent_executions:
            tree.insert('', 'end', 
                text=execution.runbook_id,
                values=(
                    execution.id[:8],
                    execution.status.value,
                    f"{execution.success_rate:.1%}",
                    execution.start_time.strftime("%H:%M:%S")
                )
            )
        
        tree.pack(fill='both', expand=True)
```

## Testing Integration

### Unit Tests

**File**: `tests/integration/test_guardian_recovery_integration.py`

```python
import pytest
import asyncio
from src.eafix.guardian.agents.risk_agent import RiskAgent
from src.eafix.guardian.agents.system_agent import SystemAgent

@pytest.mark.asyncio
async def test_risk_agent_recovery_integration():
    """Test risk agent triggers recovery correctly."""
    agent = RiskAgent()
    
    issue_data = {
        'id': 'test_position_limit',
        'risk_type': 'position_limit_exceeded',
        'severity': 'high',
        'current_exposure': 150000,
        'limit_threshold': 100000,
        'details': 'Position limit exceeded by 50%'
    }
    
    result = await agent.handle_issue(issue_data)
    
    assert 'recovery_execution_id' in result
    assert result['recovery_execution_id'] is not None

@pytest.mark.asyncio  
async def test_system_agent_recovery_integration():
    """Test system agent triggers recovery correctly."""
    agent = SystemAgent()
    
    issue_data = {
        'id': 'test_high_cpu',
        'system_issue_type': 'high_cpu_usage',
        'severity': 'critical',
        'cpu_usage': 95,
        'cpu_threshold': 80,
        'service_name': 'trading_engine'
    }
    
    result = await agent.handle_issue(issue_data)
    
    assert 'recovery_execution_id' in result
    assert result['recovery_execution_id'] is not None
```

### Integration Tests

**File**: `tests/integration/test_end_to_end_recovery.py`

```python
import pytest
import asyncio
from src.eafix.guardian.constraints.constraint_repository import ConstraintRepository

@pytest.mark.asyncio
async def test_end_to_end_constraint_recovery():
    """Test complete flow from constraint violation to recovery."""
    repo = ConstraintRepository()
    
    # Define test constraint
    constraint = {
        'id': 'test_cpu_limit',
        'type': 'cpu_usage_limit', 
        'name': 'CPU Usage Limit',
        'limit': 80
    }
    
    # Simulate violation
    violation_data = {
        'current_value': 95,
        'service_name': 'api_server'
    }
    
    result = await repo.handle_constraint_violation(constraint, violation_data)
    
    assert 'recovery_execution_id' in result
    
    # Wait for recovery to complete (with timeout)
    execution_id = result['recovery_execution_id']
    recovery_system = repo.recovery_system
    
    for _ in range(30):  # 30 second timeout
        status = recovery_system.get_execution_status(execution_id)
        if status and status.status in ['success', 'failed', 'partial']:
            break
        await asyncio.sleep(1)
    
    final_status = recovery_system.get_execution_status(execution_id)
    assert final_status.status == 'success'
```

## Configuration

### Recovery System Configuration

**File**: `src/eafix/recovery/config.py`

```python
GUARDIAN_RECOVERY_CONFIG = {
    'auto_execution_enabled': True,
    'high_risk_confirmation': True,
    'max_concurrent_recoveries': 5,
    'recovery_timeout': 600,  # 10 minutes
    'runbooks_directory': 'recovery_runbooks/guardian/',
    'agent_integration': {
        'risk_agent': {
            'auto_recovery_threshold': 'medium',
            'confirmation_required': ['position_limit_exceeded', 'margin_call']
        },
        'system_agent': {
            'auto_recovery_threshold': 'high',
            'confirmation_required': ['service_restart']
        }
    }
}
```

This integration specification provides a complete technical roadmap for transforming the Guardian system from reactive monitoring to proactive automated recovery, maintaining all existing functionality while adding powerful automation capabilities.