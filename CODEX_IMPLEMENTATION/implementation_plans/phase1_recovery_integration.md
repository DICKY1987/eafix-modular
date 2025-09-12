# Phase 1: Automated Recovery & Self-Healing Integration Plan

## Overview
Transform the CLI Multi-Rapid Enterprise Platform from 98% → 99% completion by implementing automated recovery execution and self-healing service management. This phase replaces Guardian system alerts with actual automated remediation.

## Priority: IMMEDIATE VALUE
**Impact**: Direct improvement from reactive alerts to proactive automated recovery
**Completion Target**: 99% overall system completion

## Implementation Steps

### Step 1.1: Guardian System Integration with Automated Recovery

**Target Location**: `src/eafix/recovery/`  
**Integration Point**: Existing Guardian system in `src/eafix/guardian/`

**Detailed Actions**:

1. **Create Recovery System Structure**
   ```bash
   mkdir -p src/eafix/recovery
   mkdir -p recovery_runbooks
   mkdir -p src/eafix/recovery/runbooks
   mkdir -p src/eafix/recovery/handlers
   ```

2. **Adapt Automated Recovery System**
   - Copy `source_files/automated_recovery_system.py` to `src/eafix/recovery/automated_recovery_system.py`
   - Modify imports to integrate with existing Guardian components
   - Update paths to use project-specific directories

3. **Integrate with Guardian Agents**
   ```python
   # In src/eafix/guardian/agents/risk_agent.py
   from eafix.recovery.automated_recovery_system import AutomatedRecoverySystem
   
   class RiskAgent:
       def __init__(self):
           self.recovery_system = AutomatedRecoverySystem()
           
       async def handle_alert(self, alert_data):
           # Instead of just alerting, execute recovery
           execution_id = await self.recovery_system.execute_recovery(
               alert_data['error_id'], 
               alert_data
           )
           return execution_id
   ```

4. **Create Guardian Recovery Runbooks**
   - Database connection failure runbook
   - High CPU usage runbook  
   - Memory exhaustion runbook
   - Service failure runbook
   - Network connectivity runbook

5. **Update Guardian Constraint Repository**
   ```python
   # In src/eafix/guardian/constraints/constraint_repository.py
   # Add integration hooks for recovery execution
   def trigger_recovery(self, constraint_violation):
       recovery_data = self.map_constraint_to_recovery(constraint_violation)
       return self.recovery_system.execute_recovery(
           constraint_violation.id, 
           recovery_data
       )
   ```

**Expected Files Created**:
- `src/eafix/recovery/__init__.py`
- `src/eafix/recovery/automated_recovery_system.py`
- `src/eafix/recovery/guardian_integration.py`
- `recovery_runbooks/database_connection_failure.json`
- `recovery_runbooks/high_cpu_usage.json`
- `recovery_runbooks/memory_exhaustion.json`
- `recovery_runbooks/service_failure.json`
- `recovery_runbooks/network_connectivity.json`

### Step 1.2: Self-Healing Service Manager for Microservices

**Target Location**: `eafix-modular/services/service-manager/`  
**Integration Point**: Docker Compose services in `eafix-modular/deploy/compose/`

**Detailed Actions**:

1. **Create Service Manager Microservice**
   ```bash
   mkdir -p eafix-modular/services/service-manager/src
   mkdir -p eafix-modular/services/service-manager/tests
   mkdir -p eafix-modular/services/service-manager/config
   ```

2. **Adapt Self-Healing Service Manager**
   - Copy `source_files/self_healing_service_manager.py` to `eafix-modular/services/service-manager/src/main.py`
   - Create FastAPI wrapper for service management
   - Add health endpoints for monitoring

3. **Create Service Definitions for Existing Microservices**
   ```python
   # Service definitions for all 12 microservices
   services = {
       "data-ingestor": ServiceDefinition(
           name="data-ingestor",
           command=["python", "-m", "src.main"],
           working_dir="/app/services/data-ingestor",
           restart_policy=RestartPolicy.ALWAYS,
           health_check_url="http://data-ingestor:8081/healthz",
           dependencies=["redis"]
       ),
       # ... definitions for all 12 services
   }
   ```

4. **Update Docker Compose Configuration**
   ```yaml
   # Add to eafix-modular/deploy/compose/docker-compose.yml
   service-manager:
     build: ./services/service-manager
     ports:
       - "8090:8090"
     environment:
       - REDIS_URL=redis://redis:6379
     depends_on:
       - redis
     volumes:
       - /var/run/docker.sock:/var/run/docker.sock
   ```

5. **Create Health Check Endpoints**
   - Add `/healthz` endpoints to all existing microservices
   - Implement service-specific health validation logic
   - Create unified health dashboard

6. **Update Makefile with Service Management Commands**
   ```makefile
   # Add to eafix-modular/Makefile
   service-start:
   	docker-compose exec service-manager python -c "import requests; requests.post('http://localhost:8090/services/start-all')"
   
   service-status:
   	docker-compose exec service-manager python -c "import requests; print(requests.get('http://localhost:8090/services/status').json())"
   
   service-restart:
   	docker-compose exec service-manager python -c "import requests; requests.post('http://localhost:8090/services/$(SERVICE)/restart')"
   ```

**Expected Files Created**:
- `eafix-modular/services/service-manager/src/main.py`
- `eafix-modular/services/service-manager/src/service_definitions.py`
- `eafix-modular/services/service-manager/src/health_checks.py`
- `eafix-modular/services/service-manager/requirements.txt`
- `eafix-modular/services/service-manager/Dockerfile`
- Updated `eafix-modular/deploy/compose/docker-compose.yml`
- Updated `eafix-modular/Makefile`

### Step 1.3: Cross-Language Bridge Enhancement

**Integration Point**: Existing `cross_language_bridge/` system

**Detailed Actions**:

1. **Add Recovery Integration to Bridge System**
   ```python
   # In cross_language_bridge/communication_bridge.py
   from eafix.recovery.automated_recovery_system import AutomatedRecoverySystem
   
   class CommunicationBridge:
       def __init__(self):
           self.recovery_system = AutomatedRecoverySystem()
           
       def handle_bridge_error(self, error_type, error_data):
           # Execute recovery instead of just logging
           return self.recovery_system.execute_recovery(
               f"bridge_{error_type}", 
               error_data
           )
   ```

2. **Create Bridge-Specific Recovery Runbooks**
   - MQL4 connection failure recovery
   - PowerShell execution error recovery
   - Configuration sync failure recovery

**Expected Files Modified**:
- `cross_language_bridge/communication_bridge.py`
- `cross_language_bridge/error_handler.py`
- New: `recovery_runbooks/bridge_mql4_failure.json`
- New: `recovery_runbooks/bridge_powershell_failure.json`

### Step 1.4: VS Code Integration Updates

**Target Location**: `.vscode/tasks.json` and `.vscode/launch.json`

**Detailed Actions**:

1. **Add Recovery System Tasks**
   ```json
   {
     "label": "Recovery: Test Automated System",
     "type": "shell",
     "command": "python -m src.eafix.recovery.automated_recovery_system",
     "group": "test",
     "presentation": { "panel": "new" }
   },
   {
     "label": "Recovery: List Active Executions",
     "type": "shell", 
     "command": "python -c \"from src.eafix.recovery.automated_recovery_system import AutomatedRecoverySystem; rs = AutomatedRecoverySystem(); print(rs.get_recovery_statistics())\""
   }
   ```

2. **Add Service Manager Tasks**
   ```json
   {
     "label": "Services: Start Self-Healing Manager",
     "type": "shell",
     "command": "cd eafix-modular && make service-start"
   },
   {
     "label": "Services: Check Status",
     "type": "shell",
     "command": "cd eafix-modular && make service-status"
   }
   ```

3. **Add Debug Configurations**
   ```json
   {
     "name": "Debug: Recovery System",
     "type": "python",
     "request": "launch",
     "program": "src/eafix/recovery/automated_recovery_system.py",
     "console": "integratedTerminal"
   },
   {
     "name": "Debug: Service Manager",
     "type": "python",
     "request": "launch",
     "program": "eafix-modular/services/service-manager/src/main.py",
     "console": "integratedTerminal"
   }
   ```

## Integration Testing Strategy

### Test 1: Guardian Recovery Integration
```bash
# Simulate database connection failure
python -c "
from src.eafix.guardian.agents.risk_agent import RiskAgent
agent = RiskAgent()
test_alert = {
    'error_id': 'db_connection_test',
    'error_message': 'Database connection failed',
    'system': 'database',
    'service_name': 'api_server'
}
execution_id = await agent.handle_alert(test_alert)
print(f'Recovery started: {execution_id}')
"
```

### Test 2: Self-Healing Service Manager
```bash
# Test service restart capability
cd eafix-modular
make docker-up
make service-status
# Manually stop a service
docker stop eafix-modular_data-ingestor_1
# Wait 30 seconds, verify automatic restart
sleep 30
make service-status
```

### Test 3: Cross-Language Bridge Recovery
```bash
# Test bridge error recovery
python test_cross_language_bridge.py --simulate-errors
```

## Success Criteria

**Phase 1 Complete (99% overall) when**:
- [ ] Guardian agents execute recovery instead of just alerting
- [ ] Self-healing manager automatically restarts failed microservices within 30 seconds
- [ ] Recovery runbooks execute successfully for 5 common failure scenarios
- [ ] VS Code tasks provide full recovery system control
- [ ] Zero manual intervention required for common system failures
- [ ] All existing functionality continues to work (backward compatibility)

## Risk Mitigation

**Medium Risk Items**:
1. **Service Manager Docker Socket Access**: Ensure proper permissions for container management
2. **Recovery Runbook Safety**: All recovery actions must have rollback capabilities
3. **Resource Consumption**: Monitor recovery system resource usage

**Rollback Plan**:
- Keep existing Guardian alert system as fallback
- Recovery system can be disabled via configuration flag
- All recovery actions have rollback commands

## Expected Timeline

**Development**: 2-3 days
**Testing**: 1 day  
**Integration**: 1 day
**Total**: 4-5 days

## Dependencies

- Existing Guardian system (src/eafix/guardian/)
- Microservices architecture (eafix-modular/)
- Cross-language bridge (cross_language_bridge/)
- VS Code configuration (.vscode/)

This implementation transforms the platform from reactive monitoring to proactive automated recovery, significantly improving system reliability and reducing manual intervention requirements.