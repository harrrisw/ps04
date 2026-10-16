"""Retrieve full text/media and retain immutable evidence, including timed transcripts."""
import html
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
import urllib.request
from collectors.feed_support import fetch
from lib.common import (ROOT, UTC, atomic_text, date_reason, digest, emit, jsonl, main, path,
                        read_json, rel, run_dir, save_jsonl, stage, store_call, validate_item, write_json)


def seconds(value):
    parts = value.replace(',', '.').split(':')
    return sum(float(v) * 60**i for i,v in enumerate(reversed(parts)))


def original_page_date(raw, url):
    """Read explicit original dates, never dateModified or a heuristic crawl date."""
    from lxml import html as lhtml
    from collectors.feed_support import canonical
    tree=lhtml.fromstring(raw)
    values=tree.xpath('//meta[@property="article:published_time" or @name="datePublished" or @itemprop="datePublished"]/@content')
    def article_nodes(value):
        if isinstance(value,list):
            for child in value:
                yield from article_nodes(child)
        elif isinstance(value,dict):
            types=value.get('@type',[])
            if isinstance(types,str):
                types=[types]
            if set(types) & {'Article','BlogPosting','NewsArticle','TechArticle'}:
                target=value.get('url') or value.get('mainEntityOfPage')
                if isinstance(target,dict):
                    target=target.get('@id')
                if not target or canonical(target)==canonical(url):
                    yield value.get('datePublished')
            if '@graph' in value:
                yield from article_nodes(value['@graph'])
    for script in tree.xpath('//script[@type="application/ld+json"]/text()'):
        try:
            values.extend(article_nodes(json.loads(script)))
        except (ValueError,TypeError):
            continue
    dates=[]
    for value in values:
        if isinstance(value,str):
            try:
                d=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
                dates.append(d.replace(tzinfo=UTC) if d.tzinfo is None else d.astimezone(UTC))
            except ValueError:
                pass
    return min(dates).isoformat().replace('+00:00','Z') if dates else None


def transcript(raw, suffix):
    text = raw.decode('utf-8-sig')
    segments = []
    if suffix in {'json','json3'} or text.lstrip().startswith(('{','[')):
        doc = json.loads(text)
        if isinstance(doc, dict) and 'events' in doc:
            rows = [dict(start=e['tStartMs']/1000, end=(e['tStartMs']+e.get('dDurationMs',0))/1000,
                         text=''.join(s.get('utf8','') for s in e.get('segs',[])))
                    for e in doc['events'] if 'tStartMs' in e and e.get('segs')]
        else:
            rows = doc if isinstance(doc,list) else doc.get('segments', [])
        for row in rows:
            start = row.get('start_seconds', row.get('startTime', row.get('start')))
            end = row.get('end_seconds', row.get('endTime', row.get('end')))
            segments.append(dict(start_seconds=float(start), end_seconds=float(end), text=row.get('body',row.get('text','')).strip()))
    else:
        pattern = r'(\d{1,2}:\d{2}(?::\d{2})?[.,]\d+)\s*-->\s*(\d{1,2}:\d{2}(?::\d{2})?[.,]\d+)[^\n]*\n(.*?)(?=\n\s*\n|\Z)'
        for match in re.finditer(pattern, text, re.S):
            body = html.unescape(re.sub(r'<[^>]*>', '', match[3])).strip()
            segments.append(dict(start_seconds=seconds(match[1]), end_seconds=seconds(match[2]), text=body))
    result = []
    for s in segments:
        if s['text'] and s['end_seconds'] > s['start_seconds'] >= 0:
            s['segment_id'] = f's{len(result)+1:05d}'
            result.append(s)
    if not result:
        raise RuntimeError('No timestamped transcript segments available')
    return result


def download_media(url, destination, max_bytes):
    if destination.is_file() and destination.stat().st_size > 0:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={'User-Agent':'SmallBusinessResearchBrief/1.0'})
    temp = destination.with_suffix(destination.suffix + '.part')
    try:
        with urllib.request.urlopen(request, timeout=45) as response, temp.open('wb') as out:
            total = 0
            while block := response.read(1024*1024):
                total += len(block)
                if total > max_bytes:
                    raise RuntimeError('Media exceeds configured download limit')
                out.write(block)
        os.replace(temp, destination)
    finally:
        temp.unlink(missing_ok=True)


def local_transcribe(media, settings, receipt):
    if not settings.get('allow_local_transcription', False):
        raise RuntimeError('No published timed transcript. Enable free local transcription or choose another source.')
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise RuntimeError('Install faster-whisper for local podcast/audio transcription') from e
    model_name = settings.get('whisper_model', 'base.en')
    print(f'Transcribing {media.name} locally with {model_name}; this may take several minutes.', file=sys.stderr, flush=True)
    receipt.value['tools'].append('faster-whisper')
    receipt.value['models'].append(model_name)
    model = WhisperModel(model_name, device='cpu', compute_type='int8', download_root=str(ROOT / '.tools/models'))
    parts, _ = model.transcribe(str(media), beam_size=3)
    result = []
    next_progress = 300
    for s in parts:
        if s.text.strip():
            result.append(dict(segment_id=f's{len(result)+1:05d}', start_seconds=s.start,
                               end_seconds=s.end, text=s.text.strip()))
        if s.end >= next_progress:
            print(f'Transcribed through {int(s.end)//60} minutes of {media.name}.', file=sys.stderr, flush=True)
            next_progress = s.end + 300
    return result


def extract_video(item, settings, receipt):
    import yt_dlp
    from collectors.fetch_youtube import Logger
    from lib.youtube_runtime import javascript_options
    from lib.media_tools import ffmpeg_binary
    folder = ROOT / 'data/media' / digest(item['item_id'])[:24]
    folder.mkdir(parents=True, exist_ok=True)
    opts = dict(format='bestaudio[ext=m4a]/bestaudio', outtmpl=str(folder / '%(id)s.%(ext)s'),
                quiet=True, logger=Logger(), socket_timeout=30, retries=1,
                writesubtitles=True, writeautomaticsub=True, subtitleslangs=['en','en-orig'],
                subtitlesformat='json3/vtt', max_filesize=settings.get('max_media_mb',150)*1024*1024)
    mode = settings.get('youtube_transcript_mode', 'prefer_captions')
    if mode not in {'local', 'prefer_captions'}:
        raise ValueError('youtube_transcript_mode must be local or prefer_captions')
    if mode == 'local':
        opts.update(writesubtitles=False, writeautomaticsub=False)
        receipt.value['notes'].append('Using local YouTube transcription; no caption endpoint requested: '+item['item_id'])
    opts['ffmpeg_location'] = ffmpeg_binary()
    receipt.value['tools'].append('ffmpeg')
    opts.update(javascript_options())
    receipt.value['tools'].extend(opts['js_runtimes'])
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(item['url'], download=True)
            filename = Path(ydl.prepare_filename(info))
    except yt_dlp.utils.DownloadError as e:
        if 'subtitles' not in str(e) or not settings.get('allow_local_transcription'):
            raise
        # One audio-only attempt; do not retry the rate-limited caption endpoint.
        receipt.value['notes'].append('Caption retrieval failed; using audio-only download and local transcription: '+item['item_id'])
        opts.update(writesubtitles=False,writeautomaticsub=False)
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(item['url'],download=True)
            filename = Path(ydl.prepare_filename(info))
    if not filename.is_file():
        raise RuntimeError('YouTube audio download did not complete')
    receipt.value['tools'].append('yt-dlp')
    subtitle_files = (sorted(folder.glob('*.json3')) + sorted(folder.glob('*.vtt'))) if mode != 'local' else []
    if subtitle_files:
        segments = transcript(subtitle_files[0].read_bytes(), subtitle_files[0].suffix.lstrip('.'))
        basis = 'YouTube captions; manually verify quoted segments against audio'
    else:
        segments = local_transcribe(filename, settings, receipt)
        basis = 'local speech recognition; manually verify quoted segments against audio'
    return segments, filename, basis


def execute():
    run = run_dir()
    failed = False
    with stage(run, 'extract_content') as receipt:
        candidates = jsonl(sys.stdin)
        for item in candidates:
            validate_item(item, candidate=True)
        receipt.value['input_count'] = len(candidates)
        settings = read_json(run / 'config/project.json').get('collection', {})
        as_of = read_json(run / 'run.json')['as_of_date']
        stored = {r['item_id']:r for r in store_call('list', run=run)}
        exclusions = []
        seen = {}
        overrides_file = run / 'config/evidence_overrides.json'
        overrides = read_json(overrides_file) if overrides_file.exists() else {}
        for original in candidates:
            item = dict(original)
            print('Extracting '+item['item_id']+': '+item['title'], file=sys.stderr, flush=True)
            override = overrides.get(item['item_id'], {})
            if override:
                if not override.get('reason'):
                    raise ValueError('Evidence overrides require a documented reason')
                for field in ['underlying_id','published_at','transcript_url','transcript_type']:
                    if field in override:
                        item[field] = override[field]
                item['human_metadata_correction'] = override['reason']
            reason = date_reason(item['published_at'], as_of)
            if reason:
                exclusions.append(dict(item_id=item['item_id'], version_id=None, reason=reason,
                                       detail='Not downloaded: candidate date is ineligible; ' + str(item['published_at'])))
                continue
            try:
                previous = stored.get(item['item_id'])
                if item['item_id'] in seen:
                    emit(seen[item['item_id']])
                    receipt.value['output_count'] += 1
                    continue
                segments = None
                media = None
                raw = None
                reuse = previous and all(previous.get(k) == item.get(k) for k in
                    ['title','published_at','url','media_url','underlying_id','transcript_url'])
                if item['kind'] == 'feed':
                    import trafilatura
                    raw, _, headers = fetch(item['url'])
                    original_date=original_page_date(raw,item['url'])
                    if original_date and original_date[:10] < item['published_at'][:10]:
                        item['feed_published_at']=item['published_at']
                        item['published_at']=original_date
                        item['original_publication_basis']='Earlier explicit datePublished/article:published_time on source page'
                        reuse=False
                    raw_hash = digest(raw.hex())
                    if reuse and previous.get('download_hash') == raw_hash and path(previous['text_path']).exists():
                        result = dict(previous, retrieved_at=item['retrieved_at'])
                        emit(result)
                        seen[item['item_id']] = result
                        receipt.value['output_count'] += 1
                        continue
                    text = trafilatura.extract(raw, include_comments=False, include_tables=True)
                    if not text or len(text.split()) < 120:
                        raise RuntimeError('Full substantive written content unavailable (under 120 extracted words)')
                    item['download_hash'] = raw_hash
                    receipt.value['tools'].append('trafilatura')
                elif reuse and not settings.get('refresh_media',False) and path(previous['text_path']).is_file() and path(previous['segments_path']).is_file():
                    # Media may change without metadata; refresh_media forces a fresh check.
                    result = dict(previous, retrieved_at=item['retrieved_at'])
                    emit(result)
                    seen[item['item_id']] = result
                    receipt.value['notes'].append('Reused saved media evidence for ' + item['item_id'])
                    receipt.value['output_count'] += 1
                    continue
                else:
                    if item['kind'] == 'youtube':
                        segments, media, basis = extract_video(item, settings, receipt)
                    else:
                        media = ROOT / 'data/media' / (digest(item['media_url'])[:24] + '.audio')
                        download_media(item['media_url'], media, settings.get('max_media_mb',150)*1024*1024)
                        if item.get('transcript_url'):
                            raw_transcript, _, _ = fetch(item['transcript_url'])
                            segments = transcript(raw_transcript, 'json' if 'json' in (item.get('transcript_type') or '') else 'vtt')
                            basis = 'publisher transcript; manually verify quoted segments against audio'
                        else:
                            segments = local_transcribe(media, settings, receipt)
                            basis = 'local speech recognition; manually verify quoted segments against audio'
                    if not segments or len(' '.join(s['text'] for s in segments).split()) < 120:
                        raise RuntimeError('Transcript is not substantive')
                    text = '\n'.join(s['text'] for s in segments)
                    item['transcript_basis'] = basis
                    item['media_path'] = rel(media)
                # Exact content fingerprint also permits cross-post reconciliation in review.
                item['content_hash'] = digest(re.sub(r'\s+',' ',text).strip().lower())
                version = digest(dict(title=item['title'], url=item['url'], published_at=item['published_at'],
                                      publisher_id=item['publisher_id'], kind=item['kind'], underlying_id=item.get('underlying_id'),
                                      text=text, segments=segments))
                folder = ROOT / 'data/assets' / digest(item['item_id'])[:24] / version
                folder.mkdir(parents=True, exist_ok=True)
                if not (folder / 'text.txt').exists():
                    atomic_text(folder / 'text.txt', text)
                elif (folder / 'text.txt').read_text(encoding='utf-8') != text:
                    raise RuntimeError('Immutable asset collision')
                if raw is not None and not (folder / 'source.html').exists():
                    (folder / 'source.html').write_bytes(raw)
                if segments is not None and not (folder / 'segments.json').exists():
                    write_json(folder / 'segments.json', segments)
                result = dict(item, version_id=version, text_path=rel(folder / 'text.txt'),
                              segments_path=rel(folder / 'segments.json') if segments is not None else None)
                if not (folder / 'provenance.json').exists():
                    write_json(folder / 'provenance.json', result)
                emit(result)
                seen[item['item_id']] = result
                receipt.value['output_count'] += 1
            except Exception as e:
                receipt.error(f"{item['item_id']}: {e}")
                failed = True
        save_jsonl(run / 'candidate_exclusions.jsonl', exclusions)
        receipt.value['tools'] = sorted(set(receipt.value['tools']))
    return int(failed)


if __name__ == '__main__':
    main(execute)
