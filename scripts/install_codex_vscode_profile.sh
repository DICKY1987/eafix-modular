#!/usr/bin/env bash
set -euo pipefail

MODE="merge"
BACKUP=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"; shift 2;;
    --backup)
      BACKUP="--backup"; shift;;
    *)
      shift;;
  esac
done

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

PY=python
if [[ -x .venv/bin/python ]]; then PY=.venv/bin/python; fi

$PY scripts/merge_vscode_configs.py --mode "$MODE" ${BACKUP}

echo "Done. VS Code configs updated in .vscode (mode=$MODE)."

