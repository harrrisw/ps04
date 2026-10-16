#!/usr/bin/env bash
source "$(dirname "$0")/lib/common.sh"
started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
if [[ $# -eq 0 ]]; then
  RUN_DIR="$("$PY" "$ROOT/lib/entry.py" lib.lifecycle init)" || exit $?
  export PIPELINE_RUN_DIR="$RUN_DIR"
  result=0
  bash data/store.sh init || result=$?
  if [[ $result -eq 0 ]]; then
    bash workflows/collect_sources.sh "$RUN_DIR" || result=$?
    bash workflows/create_series.sh "$RUN_DIR" || result=$?
  fi
elif [[ $# -eq 2 && "$1" == '--package' ]]; then
  RUN_DIR="$2"
  [[ -f "$RUN_DIR/run.json" ]] || { echo 'Invalid RUN_DIR' >&2; exit 2; }
  export PIPELINE_RUN_DIR="$RUN_DIR"
  result=0
  bash review/check_content.sh "$RUN_DIR" > "$RUN_DIR/review.json.tmp" || result=$?
  if [[ $result -eq 0 ]]; then
    mv "$RUN_DIR/review.json.tmp" "$RUN_DIR/review.json"
    bash publishing/prepare_package.sh "$RUN_DIR" >/dev/null || result=$?
  fi
else
  echo 'Usage: bash run.sh [--package runs/RUN_ID]' >&2
  exit 2
fi
"$PY" "$ROOT/lib/entry.py" lib.lifecycle receipt "$RUN_DIR" run "$started" "$result"
bash reporting/summarize_run.sh "$RUN_DIR" > "$RUN_DIR/summary.json.tmp" || exit $?
mv "$RUN_DIR/summary.json.tmp" "$RUN_DIR/summary.json"
cat "$RUN_DIR/summary.json"
exit "$result"
