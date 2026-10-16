#!/usr/bin/env bash
source "$(dirname "$0")/../lib/common.sh"
bash data/store.sh init || exit $?
for file in runs/*/items.jsonl; do
  [[ -f "$file" ]] || continue
  run="$(dirname "$file")"
  mode="$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["mode"])' "$run/run.json")" || exit $?
  [[ "$mode" == live ]] || continue
  bash data/store.sh upsert "$run" < "$file" > "$run/restore_changes.jsonl" || exit $?
done
echo 'Evidence index restored through the store interface.' >&2
