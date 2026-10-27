# VS Code Configuration for Codex Implementation

This directory contains VS Code configuration files optimized for the Codex enterprise improvement implementation.

## Setup Instructions

1. **Copy Configuration Files**
   ```bash
   # Copy to your .vscode directory
   cp CODEX_IMPLEMENTATION/vscode_configuration/tasks.json .vscode/
   cp CODEX_IMPLEMENTATION/vscode_configuration/launch.json .vscode/
   cp CODEX_IMPLEMENTATION/vscode_configuration/settings.json .vscode/
   ```

2. **Verify Environment Setup**
   - Ensure Python virtual environment is active
   - Install required dependencies: `pip install -r requirements.txt`
   - Start Redis server: `docker-compose -f config/docker-compose.yml up -d redis`

## Available Tasks

### Phase 1 Implementation Tasks
- **Codex: Phase 1 - Recovery System Integration** - Test recovery system import
- **Codex: Test Automated Recovery System** - Validate recovery system functionality
- **Codex: Phase 2 - Self-Healing Service Manager** - Test service manager components
- **Codex: Start Self-Healing Services** - Launch microservices with self-healing
- **Codex: Check Service Status** - Monitor service health and status

### Phase 2 & 3 Tasks
- **Codex: Phase 3 - Predictive Failure Detection** - Initialize ML-based failure prediction
- **Codex: Train Failure Prediction Models** - Train and validate ML models

### Integration Testing Tasks
- **Codex: Integration Test - Guardian Recovery** - Test Guardian-Recovery integration
- **Codex: Integration Test - Cross-Language Bridge** - Validate bridge communications
- **Codex: Full System Health Check** - Comprehensive system validation

### Utility Tasks
- **Codex: Deploy Recovery Runbooks** - Create default recovery runbooks
- **Codex: Docker Services - Start All** - Start complete Docker environment
- **Codex: Docker Services - Stop All** - Stop Docker services
- **Codex: Validate Implementation Phase 1** - Complete Phase 1 validation
- **Codex: Generate Implementation Report** - Create progress report

## Debug Configurations

### Main Components
- **Debug: Automated Recovery System** - Debug recovery system execution
- **Debug: Self-Healing Service Manager** - Debug service manager operations
- **Debug: Predictive Failure Detector** - Debug ML failure prediction
- **Debug: Guardian Risk Agent with Recovery** - Debug Guardian integration
- **Debug: Cross-Language Bridge Test** - Debug bridge communications

### Testing Configurations
- **Test: Recovery System Integration** - Run recovery system tests
- **Test: Guardian Recovery Integration** - Run Guardian integration tests
- **Test: Service Manager Self-Healing** - Run service manager tests

### Advanced Debugging
- **Attach: Running Recovery System** - Attach to running recovery system process

## Custom Settings

### Enterprise Features Enabled
- `codex.enterpriseMode`: true
- `codex.recoverySystem.enabled`: true
- `codex.selfHealing.enabled`: true
- `codex.predictiveFailure.enabled`: true
- `codex.guardianIntegration.enabled`: true

### Status Bar Integration
- **🚀 Codex Implementation Active** - Quick access to system health check
- **99% Target** - Quick access to Phase 1 validation

### Environment Variables
- `CODEX_IMPLEMENTATION_ACTIVE=true`
- `RECOVERY_SYSTEM_ENABLED=true`
- `PYTHONPATH` configured for all project modules

## File Associations

- `*.mqh` → C language (MQL4 header files)
- `*.mq4` → C language (MQL4 source files)  
- `*.ps1` → PowerShell (PowerShell scripts)

## Excluded Files

- Python cache files (`__pycache__`, `*.pyc`)
- Test artifacts (`.pytest_cache`)
- Package files (`*.egg-info`)
- Node modules (`node_modules`)

## Quick Start Workflow

1. **Initialize Recovery System**
   - Run task: "Codex: Phase 1 - Recovery System Integration"
   - Verify output shows successful import

2. **Deploy Self-Healing Services**
   - Run task: "Codex: Start Self-Healing Services" 
   - Check status with: "Codex: Check Service Status"

3. **Test Integration**
   - Run task: "Codex: Integration Test - Guardian Recovery"
   - Run task: "Codex: Integration Test - Cross-Language Bridge"

4. **Validate Phase 1**
   - Run task: "Codex: Validate Implementation Phase 1"
   - Generate report: "Codex: Generate Implementation Report"

## Troubleshooting

### Common Issues

**ImportError: No module named 'src.eafix'**
- Ensure PYTHONPATH includes `${workspaceFolder}/src`
- Check that virtual environment is active

**Redis Connection Error**
- Start Redis: `docker-compose -f config/docker-compose.yml up -d redis`
- Verify Redis URL: `redis://localhost:6379`

**Service Manager Not Starting**
- Check Docker daemon is running
- Verify eafix-modular directory exists
- Run `make docker-up` in eafix-modular directory

### Debug Tips

1. Use integrated terminal for all Python execution
2. Set breakpoints in critical recovery system functions
3. Monitor logs for detailed error messages
4. Use "Problems" panel to track code issues
5. Leverage outline view for large Python files

## Integration with Codex

These VS Code configurations are specifically designed to support Codex's implementation of enterprise improvements:

- **Task Dependencies**: Tasks are chained to ensure proper initialization order
- **Environment Setup**: All paths and variables configured for Codex workflow
- **Debug Support**: Comprehensive debugging for all major components
- **Status Monitoring**: Real-time feedback on implementation progress
- **Report Generation**: Automated progress reporting and validation

The configuration supports the three-phase implementation plan:
- **Phase 1** (98% → 99%): Recovery system and Guardian integration
- **Phase 2** (99% → 99.5%): Predictive failure detection and advanced monitoring  
- **Phase 3** (99.5% → 99.8%): Enterprise workflow orchestration and compliance

Use the status bar items for quick access to health checks and validation tasks throughout the implementation process.