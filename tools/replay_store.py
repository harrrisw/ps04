"""Record an honestly labeled unchanged replay without overwriting original changes."""
from pathlib import Path
import sys
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lib.common import coverage, now, path, read_jsonl, rel, save_jsonl, store_call, write_json

if len(sys.argv)!=2:
    raise SystemExit('Usage: python tools/replay_store.py runs/RUN_ID')
run=path(sys.argv[1])
items=read_jsonl(run/'items.jsonl')
before=store_call('list',run=run)
changes=store_call('upsert',rel(run),rows=items,run=run)
after=store_call('list',run=run)
folder=run/'replays'/('store-'+uuid.uuid4().hex[:8])
save_jsonl(folder/'changes.jsonl',changes)
write_json(folder/'replay.json',dict(mode='replay',description='Replay of exactly the saved live-run items; not a new live run',
    executed_at=now(),input_path=rel(run/'items.jsonl'),before_coverage=coverage(before),after_coverage=coverage(after),
    all_unchanged=all(r['change']=='unchanged' for r in changes),
    same_latest_versions={(r['item_id'],r['version_id']) for r in before}=={(r['item_id'],r['version_id']) for r in after}))
print(rel(folder))
