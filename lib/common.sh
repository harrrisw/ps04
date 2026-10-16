#!/usr/bin/env bash
# Shared runtime setup only; each component owns its substantive implementation.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 2
if [[ -n "${PIPELINE_PYTHON:-}" ]]; then
  PY="$PIPELINE_PYTHON"
elif [[ -x "$ROOT/.tools/python/python.exe" ]]; then
  PY="$ROOT/.tools/python/python.exe"
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUTF8=1

