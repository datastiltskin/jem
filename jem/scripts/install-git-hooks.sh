#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cp "$REPO_ROOT/jem/scripts/githooks/pre-commit" "$REPO_ROOT/.git/hooks/pre-commit"
chmod +x "$REPO_ROOT/.git/hooks/pre-commit" "$REPO_ROOT/jem/scripts/"*.sh
echo "Installed pre-commit hook"
