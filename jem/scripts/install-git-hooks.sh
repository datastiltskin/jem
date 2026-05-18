#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOK_SRC="$REPO_ROOT/jem/scripts/githooks/pre-commit"
HOOK_DST="$REPO_ROOT/.git/hooks/pre-commit"
cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST" "$REPO_ROOT/jem/scripts/"*.sh
echo "Installed pre-commit hook -> $HOOK_DST"
