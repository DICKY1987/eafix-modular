#!/usr/bin/env bash
set -euo pipefail

echo "Configuring Git hooks to use .githooks..."
git config core.hooksPath .githooks

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if [ -f .githooks/pre-push ]; then
    git update-index --chmod=+x .githooks/pre-push || true
  fi
fi

echo "Done. Hooks path set to .githooks"

