import re
from urllib.parse import urlsplit
from lib.common import evidence_text, store_call


def format_citations(markdown, items):
    # Keep internal audit markers separate from audience-facing link labels.
    def link(match):
        claim, url = match.groups()
        publisher = next((i['publisher_id'].replace('-', ' ').title() for i in items
                          if url.startswith(i['url'])), urlsplit(url).netloc.removeprefix('www.'))
        return f'[{publisher}]({url}) [claim:{claim}]'
    markdown = re.sub(r'\[claim:([^\]]+)\]\((https?://[^)]+)\)', link, markdown)
    missing = [i for i in items if i['url'] not in markdown]
    if missing or not re.search(r'\[[^\]]+\]\(https?://', markdown):
        markdown += '\n\n## Source links\n\n' + '\n'.join(
            f"- [{i['title']}]({i['url']})" for i in (items if not missing else missing))
    return markdown


def brief_evidence(run, brief):
    keys = {(e['item_id'],e['version_id']) for c in brief['claims'] for e in c['evidence']}
    return [store_call('get', *key, run=run)[0] for key in sorted(keys)]


def source_notes(brief, items):
    index = {(i['item_id'],i['version_id']):i for i in items}
    lines = []
    for claim in brief['claims']:
        lines.append(f"### {claim['claim_id']}: {claim['statement']} ({claim['type']})")
        for ref in claim['evidence']:
            item = index[(ref['item_id'],ref['version_id'])]
            locator = ref['locator']
            if locator['type'] == 'segment':
                segments = evidence_text(item)['segments']
                segment = next(s for s in segments if s['segment_id']==locator['segment_id'])
                start, end = segment['start_seconds'], segment['end_seconds']
                url = item['url'] + ('&' if '?' in item['url'] else '?') + f't={int(start)}s' if item['kind']=='youtube' else item['media_url'] + f'#t={start},{end}'
                label = f"{int(start)//60}:{int(start)%60:02d}–{int(end)//60}:{int(end)%60:02d}"
                quote = segment['text']
            else:
                url, label, quote = item['url'], 'written passage', locator['quote']
            lines.append(f"- [{item['title']}]({url}) — {item['publisher_id']}; published {item['published_at']}; {label}.\n  Evidence: {quote}")
    return '\n'.join(lines)
