# doc_id: 2026012201111001
# Setup script for combined ID System + Mapping implementation
# Created: 2026-01-22T01:11:41Z
# Usage: .\scripts\2026012201111001_setup_environment.ps1

Write-Host "🔧 Setting up environment for ID System + Mapping implementation..." -ForegroundColor Cyan

# Check Python version
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python 3 not found. Please install Python 3.10+." -ForegroundColor Red
    exit 1
}

# Check pip
try {
    python -m pip --version | Out-Null
    Write-Host "✅ pip is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ pip not found" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Yellow
$packages = @("pyyaml", "jsonschema", "pytest")

foreach ($package in $packages) {
    Write-Host "  Installing $package..." -ForegroundColor Gray
    python -m pip install --quiet --upgrade $package
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✅ $package installed" -ForegroundColor Green
    } else {
        Write-Host "    ❌ Failed to install $package" -ForegroundColor Red
    }
}

# Verify git
try {
    $gitVersion = git --version
    Write-Host "`n✅ $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "`n❌ Git not found. Please install Git." -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Environment setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Run Phase A validation: python scripts\phase_a\2026012201111002_validate_current_state.py"
