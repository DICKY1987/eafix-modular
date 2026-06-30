$ErrorActionPreference = 'Stop'

Write-Host "[bootstrap] Ensuring Python tooling..."
python --version
pip install --upgrade pip pre-commit pytest ruff mypy | Out-Host

Write-Host "[bootstrap] Installing pre-commit hooks..."
pre-commit install
pre-commit run --all-files

Write-Host "[bootstrap] Done."
