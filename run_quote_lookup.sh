#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_PYTHON="/Users/kevinfan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"

if [[ ! -x "$CODEX_PYTHON" ]]; then
  echo "找不到可用的 Codex Python runtime：$CODEX_PYTHON" >&2
  echo "請改用已安裝 openpyxl 的 Python，或先在目前環境安裝 openpyxl。" >&2
  exit 1
fi

exec "$CODEX_PYTHON" "$SCRIPT_DIR/quote_lookup.py" "$@"
