#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT="${SCRIPT_DIR}/.."
export PYTHONPATH="$REPO_ROOT/gui_terminal/src"
python -m gui_terminal.main "$@"

