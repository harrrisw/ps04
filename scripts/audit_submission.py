"""Read-only audit of retained runs, evidence files, and submission navigation.

Writes a hash inventory and reports; never changes historical run artifacts.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/audit'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def main():
    OUT.mkdir(exist_ok=True,parents=True)
    tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'))
    inventory=[]; missing=[]; referenced=set(); runs=[]
    for folder in sorted((ROOT/'runs').iterdir()):
        if not folder.is_dir() or not (folder/'run.json').exists(): continue
        summary=read(folder/'summary.json') if (folder/'summary.json').exists() else None
        runs.append(dict(run_id=folder.name,summary=summary,has_review=(folder/'review.json').exists()))
        for name in ['items.jsonl','eligible.jsonl']:
            path=folder/name
            if not path.exists(): continue
            for line in path.read_text(encoding='utf-8').splitlines():
                if not line.strip(): continue
                record=json.loads(line)
                for field in ['text_path','segments_path']:
                    ref=record.get(field)
                    if ref:
                        referenced.add(ref)
                        if not (ROOT/ref).exists(): missing.append(ref)
    for name in sorted(tracked):
        if name.startswith(('runs/','data/assets/')):
            path=ROOT/name
            if path.is_file(): inventory.append(dict(path=name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    secret_findings=[]
    for name in sorted(tracked):
        path=ROOT/name
        if path.is_file() and path.suffix in {'.json','.jsonl','.md','.txt','.py','.sh','.ps1','.log','.yaml','.yml'}:
            content=path.read_text(encoding='utf-8',errors='replace')
            # Report filenames only, never candidate key values. Ignore examples.
            for match in re.findall(r'sk-parley-v1-[A-Za-z0-9_-]{20,}',content):
                if not any(x in match.lower() for x in ['example','placeholder','your-key']): secret_findings.append(name)
    navigation=[]
    for path in [ROOT/'SUBMISSION.md',ROOT/'docs/IMPLEMENTATION.md',ROOT/'docs/RUNS.md',ROOT/'docs/CLAIM_TRACE.md',ROOT/'docs/EVALUATION.md',ROOT/'deliverables/technical-demo/README.md']:
        if not path.exists(): missing.append(str(path.relative_to(ROOT))); continue
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if link.startswith(('http:','https:','#','mailto:')): continue
            target=(path.parent/link.split('#')[0]).resolve()
            if not target.exists(): navigation.append(dict(file=str(path.relative_to(ROOT)),target=link))
    report=dict(checked_on='2026-10-16',retained_runs=len(runs),retained_hashed_files=len(inventory),referenced_evidence_files=len(referenced),missing_evidence=sorted(set(missing)),untracked_evidence=sorted(referenced-tracked),broken_local_links=navigation,possible_parley_key_files=sorted(set(secret_findings)),scope='Local structural audit; not semantic source verification, external playback, or a grading prediction')
    (OUT/'artifact_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
    (OUT/'repository_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    if missing or navigation or secret_findings or referenced-tracked: raise SystemExit(1)

if __name__=='__main__': main()
