#!/usr/bin/env bash
# Repair/retry an existing run from saved decisions, preserving prior artifacts.
source "$(dirname "$0")/../lib/common.sh"
[[ $# -ge 1 && $# -le 2 && -f "$1/decisions.jsonl" ]] || { echo 'Expected RUN_DIR [--keep-briefs] with decisions.jsonl' >&2; exit 2; }
[[ $# -eq 1 || "$2" == '--keep-briefs' ]] || { echo 'Unknown option' >&2; exit 2; }
[[ $# -eq 1 || -f "$1/briefs.jsonl" ]] || { echo '--keep-briefs requires existing corrected briefs' >&2; exit 2; }
RUN_DIR="$1"
export PIPELINE_RUN_DIR="$RUN_DIR"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive="$RUN_DIR/stage_history/$stamp"
mkdir -p "$archive"
for name in briefs.jsonl articles.jsonl video_scripts.jsonl review.json summary.json usage.jsonl; do
  [[ ! -f "$RUN_DIR/$name" ]] || cp "$RUN_DIR/$name" "$archive/$name"
done
for name in articles video_scripts; do
  [[ ! -d "$RUN_DIR/$name" ]] || cp -R "$RUN_DIR/$name" "$archive/$name"
done
result=0
if [[ $# -eq 1 ]]; then
  bash editorial/create_briefs.sh "$RUN_DIR" < "$RUN_DIR/decisions.jsonl" > "$RUN_DIR/briefs.jsonl.tmp" || result=$?
  [[ $result -ne 0 ]] || mv "$RUN_DIR/briefs.jsonl.tmp" "$RUN_DIR/briefs.jsonl"
fi
if [[ $result -eq 0 ]]; then
  bash content/write_articles.sh "$RUN_DIR" < "$RUN_DIR/briefs.jsonl" > "$RUN_DIR/articles.jsonl.tmp" || result=$?
  [[ $result -ne 0 ]] || mv "$RUN_DIR/articles.jsonl.tmp" "$RUN_DIR/articles.jsonl"
fi
if [[ $result -eq 0 ]]; then
  bash content/write_video_scripts.sh "$RUN_DIR" < "$RUN_DIR/briefs.jsonl" > "$RUN_DIR/video_scripts.jsonl.tmp" || result=$?
  [[ $result -ne 0 ]] || mv "$RUN_DIR/video_scripts.jsonl.tmp" "$RUN_DIR/video_scripts.jsonl"
fi
bash review/check_content.sh "$RUN_DIR" > "$RUN_DIR/review.json.tmp"
rc=$?
if [[ $rc -eq 0 ]]; then
  mv "$RUN_DIR/review.json.tmp" "$RUN_DIR/review.json"
  "$PY" -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1],encoding="utf-8"))["passed"] else 1)' "$RUN_DIR/review.json" || result=1
else
  result=$rc
fi
bash reporting/summarize_run.sh "$RUN_DIR" > "$RUN_DIR/summary.json.tmp" || exit $?
mv "$RUN_DIR/summary.json.tmp" "$RUN_DIR/summary.json"
cat "$RUN_DIR/summary.json"
exit "$result"
