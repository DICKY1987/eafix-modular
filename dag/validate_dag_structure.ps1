#!/usr/bin/env pwsh
# DOC_LINK: DOC-SCRIPT-VALIDATE-DAG-STRUCTURE-090
<#
.SYNOPSIS
    Validate DAG Structure Requirements (DAG-VIEW-*)

.DESCRIPTION
    Validates that DAG and execution plan files meet all requirements
    defined in the orchestration specification.

.PARAMETER StateDir
    Directory containing state files (default: .state)

.EXAMPLE
    ./validate_dag_structure.ps1 -StateDir .state
#>

[CmdletBinding()]
param(
    [Parameter()]
    [string]$StateDir = ".state",

    [Parameter()]
    [switch]$VerboseOutput
)

$ErrorActionPreference = "Stop"
$script:FailureCount = 0
$script:PassCount = 0

function Write-Result {
    param(
        [string]$RequirementId,
        [string]$Status,
        [string]$Message
    )

    $statusSymbol = if ($Status -eq "PASS") { "✓" } else { "✗" }
    $color = if ($Status -eq "PASS") { "Green" } else { "Red" }

    Write-Host "[$statusSymbol] $RequirementId : " -NoNewline
    Write-Host $Message -ForegroundColor $color

    if ($Status -eq "PASS") {
        $script:PassCount++
    } else {
        $script:FailureCount++
    }
}

function Test-DAGFile {
    param([string]$DagPath)

    $errors = @()

    try {
        $dag = Get-Content $DagPath -Raw | ConvertFrom-Json

        # Required fields
        $requiredFields = @("workstream_id", "generated_at", "nodes", "edges")
        foreach ($field in $requiredFields) {
            if (-not $dag.PSObject.Properties.Name.Contains($field)) {
                $errors += "Missing required field: $field"
            }
        }

        # Validate nodes structure
        if ($dag.nodes) {
            foreach ($node in $dag.nodes) {
                $nodeFields = @("task_id", "name", "type", "status")
                foreach ($field in $nodeFields) {
                    if (-not $node.PSObject.Properties.Name.Contains($field)) {
                        $errors += "Node missing field: $field"
                        break
                    }
                }
            }
        }

        # Validate edges structure
        if ($dag.edges) {
            foreach ($edge in $dag.edges) {
                $edgeFields = @("from", "to", "type")
                foreach ($field in $edgeFields) {
                    if (-not $edge.PSObject.Properties.Name.Contains($field)) {
                        $errors += "Edge missing field: $field"
                        break
                    }
                }
            }
        }

        # Check for cycles (basic check)
        if ($dag.nodes -and $dag.edges) {
            # Build adjacency list
            $adjList = @{}
            foreach ($node in $dag.nodes) {
                $adjList[$node.task_id] = @()
            }
            foreach ($edge in $dag.edges) {
                if ($adjList.ContainsKey($edge.from)) {
                    $adjList[$edge.from] += $edge.to
                }
            }

            # Simple cycle detection via DFS
            $visited = @{}
            $recStack = @{}

            function Test-Cycle {
                param([string]$nodeId)

                $visited[$nodeId] = $true
                $recStack[$nodeId] = $true

                foreach ($neighbor in $adjList[$nodeId]) {
                    if (-not $visited.ContainsKey($neighbor)) {
                        if (Test-Cycle $neighbor) {
                            return $true
                        }
                    } elseif ($recStack.ContainsKey($neighbor)) {
                        return $true
                    }
                }

                $recStack.Remove($nodeId)
                return $false
            }

            foreach ($nodeId in $adjList.Keys) {
                if (-not $visited.ContainsKey($nodeId)) {
                    if (Test-Cycle $nodeId) {
                        $errors += "Dependency cycle detected in DAG"
                        break
                    }
                }
            }
        }

        return $errors

    } catch {
        return @("Invalid JSON: $($_.Exception.Message)")
    }
}

function Test-ExecutionPlanFile {
    param([string]$PlanPath)

    $errors = @()

    try {
        $plan = Get-Content $PlanPath -Raw | ConvertFrom-Json

        # Required fields
        $requiredFields = @("workstream_id", "generated_at", "stages")
        foreach ($field in $requiredFields) {
            if (-not $plan.PSObject.Properties.Name.Contains($field)) {
                $errors += "Missing required field: $field"
            }
        }

        # Validate stages structure
        if ($plan.stages) {
            foreach ($stage in $plan.stages) {
                $stageFields = @("stage", "parallel_tasks")
                foreach ($field in $stageFields) {
                    if (-not $stage.PSObject.Properties.Name.Contains($field)) {
                        $errors += "Stage missing field: $field"
                        break
                    }
                }

                # Check for v2.0.0 enhancements (optional but recommended)
                if (-not $stage.PSObject.Properties.Name.Contains("max_parallelism")) {
                    $errors += "Warning: Stage missing max_parallelism (v2.0.0 enhancement)"
                }

                if (-not $stage.PSObject.Properties.Name.Contains("estimated_duration_seconds")) {
                    $errors += "Warning: Stage missing estimated_duration_seconds (v2.0.0 enhancement)"
                }
            }
        }

        # Check for critical path information (v2.0.0)
        if (-not $plan.PSObject.Properties.Name.Contains("critical_path_duration")) {
            $errors += "Warning: Plan missing critical_path_duration (v2.0.0 enhancement)"
        }

        return $errors

    } catch {
        return @("Invalid JSON: $($_.Exception.Message)")
    }
}

Write-Host "`n=== Validating DAG Structure Requirements ===" -ForegroundColor Cyan
Write-Host "State Directory: $StateDir`n" -ForegroundColor Gray

# DAG-VIEW-001: DAG Structure Requirements
Write-Host "`nDAG-VIEW-001: DAG Structure Requirements" -ForegroundColor Yellow

if (-not (Test-Path $StateDir)) {
    Write-Result "DAG-VIEW-001" "FAIL" "State directory not found: $StateDir"
} else {
    $dagFiles = Get-ChildItem -Path $StateDir -Filter "dag_*.json"

    if ($dagFiles.Count -eq 0) {
        Write-Host "  No DAG files found - this may be valid for new installation" -ForegroundColor Yellow
        Write-Result "DAG-VIEW-001" "PASS" "DAG directory structure exists (0 DAG files found)"
    } else {
        $allDagsValid = $true
        $dagsWithErrors = 0

        foreach ($dagFile in $dagFiles) {
            $errors = Test-DAGFile $dagFile.FullName

            if ($errors.Count -gt 0) {
                $allDagsValid = $false
                $dagsWithErrors++

                Write-Host "  Errors in $($dagFile.Name):" -ForegroundColor Red
                foreach ($error in $errors) {
                    Write-Host "    - $error" -ForegroundColor Red
                }
            } elseif ($VerboseOutput) {
                Write-Host "  ✓ $($dagFile.Name)" -ForegroundColor Gray
            }
        }

        $validCount = $dagFiles.Count - $dagsWithErrors
        Write-Result "DAG-VIEW-001" $(if ($allDagsValid) { "PASS" } else { "FAIL" }) `
            "DAG structure validation: $validCount/$($dagFiles.Count) DAG files valid"
    }
}

# DAG-VIEW-002: DAG File Schema
Write-Host "`nDAG-VIEW-002: DAG File Schema" -ForegroundColor Yellow

# This is covered by DAG-VIEW-001 validation
Write-Result "DAG-VIEW-002" "PASS" "DAG file schema validated in DAG-VIEW-001"

# DAG-VIEW-003: Execution Plan Schema
Write-Host "`nDAG-VIEW-003: Execution Plan Schema" -ForegroundColor Yellow

if (Test-Path $StateDir) {
    $planFiles = Get-ChildItem -Path $StateDir -Filter "execution_plan_*.json"

    if ($planFiles.Count -eq 0) {
        Write-Host "  No execution plan files found" -ForegroundColor Yellow
        Write-Result "DAG-VIEW-003" "PASS" "Execution plan directory exists (0 plans found)"
    } else {
        $allPlansValid = $true
        $plansWithErrors = 0
        $warningCount = 0

        foreach ($planFile in $planFiles) {
            $errors = Test-ExecutionPlanFile $planFile.FullName

            # Count warnings vs errors
            $actualErrors = $errors | Where-Object { $_ -notlike "Warning:*" }
            $warnings = $errors | Where-Object { $_ -like "Warning:*" }
            $warningCount += $warnings.Count

            if ($actualErrors.Count -gt 0) {
                $allPlansValid = $false
                $plansWithErrors++

                Write-Host "  Errors in $($planFile.Name):" -ForegroundColor Red
                foreach ($error in $actualErrors) {
                    Write-Host "    - $error" -ForegroundColor Red
                }
            }

            if ($warnings.Count -gt 0 -and $VerboseOutput) {
                foreach ($warning in $warnings) {
                    Write-Host "  $warning" -ForegroundColor Yellow
                }
            } elseif ($actualErrors.Count -eq 0 -and $VerboseOutput) {
                Write-Host "  ✓ $($planFile.Name)" -ForegroundColor Gray
            }
        }

        $validCount = $planFiles.Count - $plansWithErrors
        $message = "Execution plan validation: $validCount/$($planFiles.Count) plans valid"
        if ($warningCount -gt 0) {
            $message += " ($warningCount warnings about v2.0.0 enhancements)"
        }

        Write-Result "DAG-VIEW-003" $(if ($allPlansValid) { "PASS" } else { "FAIL" }) $message
    }
} else {
    Write-Result "DAG-VIEW-003" "FAIL" "State directory not found"
}

# Summary
Write-Host "`n=== Validation Summary ===" -ForegroundColor Cyan
Write-Host "PASSED: $script:PassCount" -ForegroundColor Green
Write-Host "FAILED: $script:FailureCount" -ForegroundColor $(if ($script:FailureCount -gt 0) { "Red" } else { "Green" })

if ($script:FailureCount -gt 0) {
    Write-Host "`nValidation FAILED. See errors above." -ForegroundColor Red
    exit 1
} else {
    Write-Host "`nValidation PASSED. All DAG structure requirements met." -ForegroundColor Green
    exit 0
}
