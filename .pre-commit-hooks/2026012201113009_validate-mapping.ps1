# doc_id: 2026012201113009
# Pre-Commit Hook: Validate Mapping System
# Created: 2026-01-22T01:36:17Z
# Usage: Run automatically before git commit, or manually

Write-Host "🔍 Validating file-step-module mapping..." -ForegroundColor Cyan

# Run all validators
$validatorScript = "scripts\validators\2026012201111009_run_all_validators.py"
$bidirectionalScript = "scripts\validators\2026012201113008_validate_bidirectional_mapping.py"

if (-not (Test-Path $validatorScript)) {
    Write-Host "❌ Master validator not found: $validatorScript" -ForegroundColor Red
    exit 1
}

# Run master validators
Write-Host "`nRunning master validators..." -ForegroundColor Yellow
python $validatorScript
$masterResult = $LASTEXITCODE

# Run bidirectional validator
if (Test-Path $bidirectionalScript) {
    Write-Host "`nRunning bidirectional validator..." -ForegroundColor Yellow
    python $bidirectionalScript
    $bidirectionalResult = $LASTEXITCODE
} else {
    Write-Host "⚠️  Bidirectional validator not found, skipping" -ForegroundColor Yellow
    $bidirectionalResult = 0
}

# Summary
Write-Host "`n" + ("="*60) -ForegroundColor Cyan
if ($masterResult -eq 0 -and $bidirectionalResult -eq 0) {
    Write-Host "✅ ALL MAPPING VALIDATIONS PASSED" -ForegroundColor Green
    Write-Host "Safe to commit." -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ MAPPING VALIDATION FAILED" -ForegroundColor Red
    Write-Host "Please fix errors before committing." -ForegroundColor Red
    Write-Host "To bypass (not recommended): git commit --no-verify" -ForegroundColor Yellow
    exit 1
}
