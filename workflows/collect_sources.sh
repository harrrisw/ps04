#!/usr/bin/env bash
source "$(dirname "$0")/../lib/common.sh"
[[ $# -eq 1 && -f "$1/run.json" ]] || { echo 'Expected RUN_DIR' >&2; exit 2; }
RUN_DIR="$1"
export PIPELINE_RUN_DIR="$RUN_DIR"
started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
result=0
mkdir -p "$RUN_DIR/candidates"
for kind in feeds youtube podcasts; do
  bash "collectors/fetch_${kind}.sh" "$RUN_DIR" > "$RUN_DIR/candidates/$kind.jsonl" || result=$?
done
cat "$RUN_DIR"/candidates/{feeds,youtube,podcasts}.jsonl > "$RUN_DIR/candidates.jsonl"
# A real pipe connects the combined discovery stream to extraction.
cat "$RUN_DIR/candidates.jsonl" | bash processing/extract_content.sh "$RUN_DIR" > "$RUN_DIR/items.jsonl" || result=$?
bash data/store.sh upsert "$RUN_DIR" < "$RUN_DIR/items.jsonl" > "$RUN_DIR/changes.jsonl" || result=$?
bash data/store.sh list > "$RUN_DIR/corpus.jsonl" || result=$?
bash processing/filter_items.sh "$RUN_DIR" < "$RUN_DIR/corpus.jsonl" > "$RUN_DIR/eligible.jsonl" || result=$?
"$PY" "$ROOT/lib/entry.py" lib.lifecycle receipt "$RUN_DIR" collect_sources "$started" "$result"
exit "$result"
