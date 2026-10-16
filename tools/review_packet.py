"""Prepare readable, unapproved review materials from real generated artifacts."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from content.support import brief_evidence, source_notes
from lib.common import atomic_text, path, read_json, read_jsonl

if len(sys.argv) not in {2,3}:
    raise SystemExit('Usage: python tools/review_packet.py runs/RUN_ID [decision-sample-path]')
run=path(sys.argv[1])
review=read_json(run/'review.json')
briefs=read_jsonl(run/'briefs.jsonl')
lines=['# Editorial review packet — student approval pending\n',
       'These are drafts, not published articles or rendered videos. Read each pair and its source notes before deciding whether to approve.\n',
       f"Mechanical checks passed: **{review['passed']}**.\n\nCurrent review ID: `{review['review_id']}`.\n",
       '| Piece | Article draft | Google Vids script | Supporting passages |\n| --- | --- | --- | --- |']
for brief in briefs:
    pid=brief['piece_id']
    evidence=brief_evidence(run,brief)
    atomic_text(run/'review_materials'/(pid+'-sources.md'),source_notes(brief,evidence)+'\n')
    lines.append(f"| {pid}: {brief['title']} | [Read article](articles/{pid}.md) | [Read script](video_scripts/{pid}.md) | [Sources and timestamps](review_materials/{pid}-sources.md) |")
lines += ['\n## Checks requiring attention\n']
for item in review['issues']:
    lines.append(f"- **{item['severity']} — {item['artifact']}:** {item['explanation']}")
import os
sample = path(sys.argv[2]) if len(sys.argv)==3 else run/'human_review_sample.md'
sample_link = Path(os.path.relpath(sample,run)).as_posix()
lines += ['\n## Your review\n',
          f'- [Complete the six-item decision sample]({sample_link}).' if sample.exists() else '- Create the decision worksheet using `tools/review_sample.py` and complete it.',
          '- [Compare the revised policy and decisions](comparison.md).',
          '- [Review source usage by piece](usage.jsonl).',
          '- [Follow the student approval instructions](../../docs/HUMAN_REVIEW.md).',
          '\nOnly the student supplies approval. Check SUBMISSION.md for the actual run dates and outstanding Google Vids production, publication, and technical demonstration.\n']
atomic_text(run/'REVIEW.md','\n'.join(lines))
print(run/'REVIEW.md')
