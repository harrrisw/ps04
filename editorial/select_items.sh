#!/usr/bin/env bash
source "$(dirname "$0")/../lib/common.sh"
exec "$PY" "$ROOT/lib/entry.py" editorial.select_items "$@"
