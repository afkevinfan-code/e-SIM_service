#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_PYTHON="/Users/kevinfan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"

if [[ -x "$CODEX_PYTHON" ]]; then
  exec "$CODEX_PYTHON" "$SCRIPT_DIR/support_server.py" "$@"
fi

exec python3 "$SCRIPT_DIR/support_server.py" "$@"
