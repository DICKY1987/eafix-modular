# Predetermined Workflow Framework - Usage Guide

## Quick Start

```bash
# 1. Initialize the framework
pwsh scripts/setup-workflows.ps1 -Command init

# 2. Run a predetermined Python edit workflow
pwsh scripts/orchestrator.ps1 -Command run-workflow -WorkflowId PY_EDIT_V2 \
  -Files "src/auth.py,src/models/user.py" \
  -Prompt "Add OAuth2 authentication support with proper error handling"

# 3. Check constraint status
pwsh scripts/constraint-engine.ps1 -ConstraintSet pre_execution \
  -Files "src/auth.py" -Verbose
```

## Core Concepts

### 1. Predetermined Workflows
Every workflow is **completely defined** in YAML - no runtime decisions about process flow:

```yaml
# The workflow ALWAYS follows these exact steps
steps:
  - Initialize Context (always)
  - Evaluate Constraints (always) 
  - Route to Tool (deterministic based on constraints)
  - Execute Edit (tool-specific but predetermined)
  - Validate Quality (always)
  - Commit & Push (always)
```

### 2. Constraint-Based Routing
The **only** variability is which tool executes the edit, determined by constraints:

```
Files: src/auth.py, src/user.py (2 files, 450 lines total)
Constraints: ✅ Git clean, ✅ Paths allowed, ✅ Size OK, ✅ Syntax valid
Result: → aider_local (predetermined choice for this scenario)

Files: src/*.py (15 files, 3000 lines total)  
Constraints: ✅ Git clean, ❌ Too many files
Result: → vscode_editor (predetermined fallback)
```

### 3. Repeatable Execution
Same inputs + same constraints = same tool selection = same process flow.

## Workflow Scenarios

### Scenario 1: Simple Python Refactoring
```bash
# Input: 1-3 Python files, <500 lines total, clean git state
pwsh scripts/orchestrator.ps1 -Command run-workflow -WorkflowId PY_EDIT_V2 \
  -Files "src/utils.py" \
  -Prompt "Extract helper functions into separate utility classes"

# Predetermined path:
# 1. ✅ Constraints pass (small, clean)
# 2. → Route to aider_local (predetermined for simple cases)
# 3. → CLI: aider --model ollama/codellama:7b-instruct --yes src/utils.py
# 4. → Quality checks: ruff, mypy, pytest
# 5. → Commit with prefix: "py-edit: Extract helper functions..."
```

### Scenario 2: Complex Multi-File Changes
```bash
# Input: 8+ Python files, >2000 lines total
pwsh scripts/orchestrator.ps1 -Command run-workflow -WorkflowId PY_EDIT_V2 \
  -Files "src/models/*.py,src/api/*.py" \
  -Prompt "Refactor authentication system to use dependency injection"

# Predetermined path:
# 1. ✅ Constraints pass but large changeset detected
# 2. → Route to claude_code (predetermined for complex cases)
# 3. → CLI: claude --strategy code --files src/models/*.py,src/api/*.py
# 4. → Quality checks (same)
# 5. → Commit (same)
```

### Scenario 3: Constraint Violations
```bash
# Input: Files outside allowed paths OR dirty git state
pwsh scripts/orchestrator.ps1 -Command run-workflow -WorkflowId PY_EDIT_V2 \
  -Files "migrations/001_initial.py" \
  -Prompt "Fix migration schema"

# Predetermined path:
# 1. ❌ Constraint violation: migrations/ not in allowlist
# 2. → Route to vscode_editor (predetermined fallback)
# 3. → Open VS Code: code --reuse-window migrations/001_initial.py
# 4. → Wait for manual commit matching "py-edit:" pattern
# 5. → Quality checks (same)
```

## Constraint Configuration

### Adding New Constraints
Edit `.ai/constraints/config.yaml`:

```yaml
constraints:
  file_validation:
    - id: files.no_test_changes_without_tests
      name: "Tests Required for Logic Changes"
      type: custom.test_coverage_check
      severity: HARD_BLOCK
      description: "Logic changes must include corresponding tests"
      params:
        require_tests_for:
          - "src/models/**"
          - "src/api/**"
        test_patterns:
          - "tests/**/test_*.py"
          - "tests/**/*_test.py"
```

### Custom Constraint Types
Implement new constraint evaluators in `constraint-engine.ps1`:

```powershell
[hashtable] CheckTestCoverage([string[]]$files, [hashtable]$params) {
    $result = @{ passed = $true; message = ""; reasoning = "" }
    
    $logicFiles = $files | Where-Object { $_ -like "src/models/*" -or $_ -like "src/api/*" }
    
    foreach ($file in $logicFiles) {
        $testFile = $file -replace "src/", "tests/" -replace "\.py$", "_test.py"
        if (-not (Test-Path $testFile)) {
            $result.passed = $false
            $result.message = "Missing test file: $testFile for $file"
            $result.reasoning = "Logic changes require corresponding tests"
            break
        }
    }
    
    return $result
}
```

## Advanced Usage

### Creating Custom Workflows
Create new workflow definition in `.ai/workflows/`:

```yaml
# .ai/workflows/api_update.yaml
version: 2
metadata:
  id: API_UPDATE
  name: "API Endpoint Update Workflow"

triggers:
  manual:
    inputs:
      - name: api_files
        type: globs
        validation: "src/api/**/*.py"
      - name: update_type
        type: enum
        values: ["new_endpoint", "modify_existing", "deprecate"]

constraints:
  include: ["api_specific.yaml"]

steps:
  - id: "1.001"
    name: "Validate API Schema"
    actor: system
    actions:
      - type: validate_openapi_schema
      - type: check_breaking_changes
  
  - id: "1.002" 
    name: "Update API Implementation"
    actor: "{{selected_tool}}"
    # ... rest of workflow
```

### Parallel Workflow Execution
```bash
# Run multiple workflows in parallel
pwsh scripts/orchestrator.ps1 -Command run-parallel \
  -Workflows "PY_EDIT_V2,API_UPDATE,SECURITY_SCAN" \
  -Files "src/auth.py,src/api/auth.py,src/models/user.py"
```

### Workflow Composition
```yaml
# .ai/workflows/full_feature.yaml
version: 2
metadata:
  id: FULL_FEATURE
  name: "Complete Feature Implementation"

composed_workflows:
  - workflow: PY_EDIT_V2
    stage: implementation
    inputs:
      files: "{{feature_files}}"
      prompt: "{{implementation_prompt}}"
  
  - workflow: API_UPDATE  
    stage: api_changes
    inputs:
      api_files: "{{api_files}}"
      update_type: "new_endpoint"
  
  - workflow: SECURITY_SCAN
    stage: validation
    inputs:
      scan_files: "{{all_changed_files}}"
```

## Monitoring & Debugging

### Real-Time Workflow Status
```bash
# Watch workflow execution
pwsh scripts/orchestrator.ps1 -Command watch -WorkflowId PY_EDIT_V2

# Sample output:
# 🚀 Workflow: PY_EDIT_V2 [RUNNING]
# ├── 1.001 Initialize Context ✅ (0.2s)
# ├── 1.002 Evaluate Constraints ✅ (1.1s) → aider_local
# ├── 1.003 Execute Primary Path 🔄 (30s elapsed)
# ├── 1.004 Execute Fallback [SKIPPED]
# ├── 1.005 Quality Validation [PENDING]
# └── 1.006 Finalize & Commit [PENDING]
```

### Constraint Analysis
```bash
# Deep dive into constraint evaluation
pwsh scripts/constraint-engine.ps1 -ConstraintSet pre_execution \
  -Files "src/complex_module.py" -Verbose

# Output shows decision reasoning:
# 🔍 Evaluating constraint set: pre_execution
# 📁 Files: src/complex_module.py
# 
# 📊 Constraint Evaluation Results:
#   Selected Tool: claude_code
#   Violations: 0
#   Warnings: 2
#   Duration: 1,234ms
# 
# ⚠️  Warnings:
#   [SOFT_WARN] complexity.cyclomatic: Function 'process_data' complexity: 12 > 10
#   [SOFT_WARN] quality.type_hints: Missing type hints in 3 functions
# 
# 🧠 Reasoning:
#   [git.clean_worktree] Git worktree is clean
#   [files.count_limit] File count (1) within limit (12)
#   [complexity.cyclomatic] High complexity detected, suggesting sophisticated tool
#   [tool_selection] Large file (847 lines) + complexity → claude_code
```

### Workflow Metrics
```bash
# View workflow performance metrics
pwsh scripts/orchestrator.ps1 -Command metrics -Days 7

# Tool Selection Frequency (Last 7 Days):
#   aider_local: 67% (134 workflows)
#   vscode_editor: 28% (56 workflows)  
#   claude_code: 5% (10 workflows)
# 
# Average Duration by Tool:
#   aider_local: 2m 14s
#   claude_code: 4m 32s
#   vscode_editor: 15m 27s (includes manual time)
# 
# Constraint Violation Rate: 12%
#   Most Common: files.count_limit (8%)
#   Second: git.clean_worktree (3%)
```

## Best Practices

### 1. Design for Determinism
- **Always** define complete workflows in YAML
- **Never** make process decisions in PowerShell scripts
- Use constraints for **tool selection only**, not process flow

### 2. Constraint Strategy
- Start with **strict constraints** and relax as needed
- Use `HARD_BLOCK` for safety (git clean, path restrictions)
- Use `SOFT_WARN` for quality guidance (complexity, style)

### 3. Tool Selection Logic
- **aider_local**: Simple edits, <5 files, <1000 lines total
- **claude_code**: Complex logic, >5 files, >1000 lines total  
- **vscode_editor**: Any constraint violations or special cases

### 4. Monitoring
- Track tool selection frequency to tune constraints
- Monitor violation rates to identify workflow friction
- Use metrics to optimize constraint thresholds

This framework gives you **100% predetermined workflows** with **intelligent tool routing** - the best of both worlds!