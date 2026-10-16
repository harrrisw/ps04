"""Shared feed parsing for written RSS and podcast RSS, not their orchestration."""
import calendar
import datetime as dt
import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import urllib.request
import feedparser
from lib.common import UTC, now


def fetch(url, limit=12_000_000):
    request = urllib.request.Request(url, headers={'User-Agent': 'SmallBusinessResearchBrief/1.0 (educational research)',
                                                 'Accept': 'application/rss+xml, application/atom+xml, text/html, */*'})
    with urllib.request.urlopen(request, timeout=35) as response:
        content = response.read(limit + 1)
        if len(content) > limit:
            raise RuntimeError('Response exceeded configured size limit')
        return content, response.geturl(), dict(response.headers)


def canonical(url):
    parts = urlsplit(url)
    query = [(k,v) for k,v in parse_qsl(parts.query) if not k.startswith('utm_') and k not in {'fbclid','gclid'}]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip('/') or '/', urlencode(query), ''))


def candidates(source):
    raw, _, _ = fetch(source['url'])
    doc = feedparser.parse(raw)
    if not doc.get('version') or (doc.bozo and not doc.entries):
        raise RuntimeError('Endpoint is not a readable RSS/Atom feed')
    rows = []
    for entry in doc.entries[:source.get('max_items', 12)]:
        media = next((l.get('href') for l in entry.get('links', []) if l.get('rel') == 'enclosure'
                      and (l.get('type','').startswith('audio/') or source['kind'] == 'podcast')), None)
        url = canonical(entry.get('link') or media or '')
        if not url:
            continue
        stamp = entry.get('published_parsed')
        # updated is deliberately not a substitute for original publication time.
        published = dt.datetime.fromtimestamp(calendar.timegm(stamp), UTC).isoformat().replace('+00:00','Z') if stamp else None
        native = entry.get('id') or url
        identity = canonical(media) if source['kind'] == 'podcast' and media else native
        item_id = source['kind'] + ':' + hashlib.sha256(identity.encode()).hexdigest()[:24]
        transcript = entry.get('podcast_transcript')
        if isinstance(transcript, list):
            transcript = next((t for t in transcript if t.get('type') in {'application/json','text/vtt','application/srt'}), None)
        row = dict(item_id=item_id, source_id=source['source_id'], publisher_id=source['publisher_id'],
                   kind=source['kind'], title=entry.get('title','Untitled'), url=url, published_at=published,
                   retrieved_at=now(), media_url=media, native_id=native, underlying_id=item_id,
                   original_publication_basis='feed published field',
                   transcript_url=transcript.get('url') if isinstance(transcript, dict) else None,
                   transcript_type=transcript.get('type') if isinstance(transcript, dict) else None)
        rows.append(row)
    return rows
