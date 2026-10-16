"""Create a combined reading copy; original drafts and approval remain untouched."""
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.common import PIECES, atomic_text, path

if len(sys.argv) != 2:
    raise SystemExit('Usage: python tools/article_preview.py runs/RUN_ID')
run = path(sys.argv[1])
sections = [
    '# Three articles for feedback\n',
    'These are the existing, unapproved drafts, dated October 10, 2026. '
    'Internal claim markers are hidden in this reading copy; original drafts retain '
    'them. Source links and article wording are preserved. No research refresh or '
    'LLM regeneration was performed for this preview.\n',
    'Give feedback by article and paragraph, for example: '
    '“02-P03: make this less technical.” Feedback can also cover the whole series.\n',
]
for pid in PIECES:
    original = (run/'articles'/f'{pid}.md').read_text(encoding='utf-8')
    title, body = original.split('\n', 1)
    sections.append(f'## Article {pid}: {title.removeprefix("# ")}\n')
    sections.append(f'[Original draft with claim markers](articles/{pid}.md)\n')
    body = re.sub(r'\s*\[claim:[^\]]+\]', '', body)
    paragraph = 0
    for block in body.strip().split('\n\n'):
        if block.startswith('## '):
            block = '#'+block
        elif not block.startswith(('*', '-', '1.')):
            paragraph += 1
            block = f'**{pid}-P{paragraph:02d}** {block}'
        sections.append(block+'\n')
atomic_text(run/'ARTICLE_PREVIEW.md', '\n'.join(sections))
print(run/'ARTICLE_PREVIEW.md')
