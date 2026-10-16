"""Prepare an unfilled student worksheet; never supplies human judgments."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lib.common import atomic_text, path, read_jsonl

if len(sys.argv)!=2:
    raise SystemExit('Usage: python tools/review_sample.py runs/RUN_ID')
run=path(sys.argv[1])
decisions=read_jsonl(run/'decisions.jsonl')
items={(r['item_id'],r['version_id']):r for r in read_jsonl(run/'eligible.jsonl')}
selected=[d for d in decisions if d['decision']=='accept'][:3]
selected += [d for d in decisions if d['decision'] in {'reject','defer'}][:3]
target=run/'human_review_sample.md'
if target.exists():
    raise SystemExit('Worksheet already exists; preserve the student’s answers.')
parts=['# Student editorial review — answers pending\n',
       'Compare the actual evidence and AI reasons. This worksheet is not a completed review.\n']
for d in selected:
    item=items[(d['item_id'],d['version_id'])]
    parts.append(f"## {item['title']}\n\n- Item: `{d['item_id']}` / `{d['version_id']}`\n- Source: {item['url']}\n- AI decision: {d['decision']}\n- AI reason: {d['reason']}\n\n**My decision and reasoning:** TO COMPLETE\n\n**Evidence checked / disagreement / correction:** TO COMPLETE\n")
if len(selected)<6 or sum(d['decision']=='accept' for d in selected)<3:
    parts.append('**Incomplete sample:** collect enough candidates for three accepted and three rejected/deferred reviews.\n')
parts.append('## Policy revision\n\n**Rule changed and why:** TO COMPLETE\n\n**Before/after run paths and effects:** TO COMPLETE\n')
atomic_text(target,'\n'.join(parts))
print(target)
