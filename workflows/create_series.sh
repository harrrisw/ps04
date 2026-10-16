#!/usr/bin/env bash
source "$(dirname "$0")/../lib/common.sh"
[[ $# -eq 1 && -f "$1/run.json" ]] || { echo 'Expected RUN_DIR' >&2; exit 2; }
RUN_DIR="$1"
export PIPELINE_RUN_DIR="$RUN_DIR"
started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
result=0
run_stage() {
  local component="$1" input="$2" output="$3"
  bash "$component" "$RUN_DIR" < "$RUN_DIR/$input" > "$RUN_DIR/$output.tmp"
  local rc=$?
  if [[ $rc -eq 0 ]]; then
    mv "$RUN_DIR/$output.tmp" "$RUN_DIR/$output"
  else
    result=$rc
  fi
}
if [[ ! -f "$RUN_DIR/eligible.jsonl" ]]; then
  result=1
else
  run_stage editorial/select_items.sh eligible.jsonl decisions.jsonl
  [[ $result -ne 0 ]] || run_stage editorial/create_briefs.sh decisions.jsonl briefs.jsonl
  [[ $result -ne 0 ]] || run_stage content/write_articles.sh briefs.jsonl articles.jsonl
  [[ $result -ne 0 ]] || run_stage content/write_video_scripts.sh briefs.jsonl video_scripts.jsonl
fi
# Always assess the available artifacts, even after a failed generation stage.
bash review/check_content.sh "$RUN_DIR" > "$RUN_DIR/review.json.tmp"
rc=$?
if [[ $rc -eq 0 ]]; then
  mv "$RUN_DIR/review.json.tmp" "$RUN_DIR/review.json"
  "$PY" -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1],encoding="utf-8"))["passed"] else 1)' "$RUN_DIR/review.json" || result=1
else
  result=$rc
fi
"$PY" "$ROOT/lib/entry.py" lib.lifecycle receipt "$RUN_DIR" create_series "$started" "$result"
exit "$result"
