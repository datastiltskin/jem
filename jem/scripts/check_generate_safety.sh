#!/usr/bin/env bash
# Show git diff under jem/data after a generate run.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
echo "=== git diff jem/data (after generate) ==="
git -C "$REPO_ROOT" diff --stat -- jem/data/ || true
