import datetime as dt
import sys
import yt_dlp
from lib.common import UTC, emit, main, now, read_json, run_dir, stage
from lib.youtube_runtime import javascript_options


class Logger:
    def debug(self, msg):
        pass
    def warning(self, msg):
        print(msg, file=sys.stderr)
    def error(self, msg):
        print(msg, file=sys.stderr)


def execute():
    run = run_dir()
    failed = False
    with stage(run, 'fetch_youtube') as receipt:
        sources = [s for s in read_json(run / 'config/sources.json') if s['kind'] == 'youtube']
        receipt.value['input_count'] = len(sources)
        receipt.value['tools'].append('yt-dlp')
        for source in sources:
            opts = dict(quiet=True, skip_download=True, extract_flat='in_playlist',
                        playlistend=source.get('max_items',4), socket_timeout=25,
                        retries=1, extractor_retries=1, logger=Logger())
            try:
                opts.update(javascript_options())
                receipt.value['tools'].extend(opts['js_runtimes'])
                with yt_dlp.YoutubeDL(opts) as ydl:
                    result = ydl.extract_info(source['url'], download=False)
                    entries = result.get('entries', [result])
                    for entry in entries:
                        if not entry:
                            continue
                        try:
                            info = entry if entry.get('upload_date') else ydl.extract_info(
                                f"https://www.youtube.com/watch?v={entry['id']}", download=False)
                            stamp = info.get('release_timestamp') or info.get('timestamp')
                            if stamp:
                                published = dt.datetime.fromtimestamp(stamp, UTC).isoformat().replace('+00:00','Z')
                            elif info.get('upload_date'):
                                published = dt.datetime.strptime(info['upload_date'], '%Y%m%d').replace(tzinfo=UTC).isoformat().replace('+00:00','Z')
                            else:
                                published = None
                            item_id = 'youtube:' + info['id']
                            emit(dict(item_id=item_id, source_id=source['source_id'], publisher_id=source['publisher_id'],
                                      kind='youtube', title=info['title'], url=f"https://www.youtube.com/watch?v={info['id']}",
                                      published_at=published, retrieved_at=now(), media_url=None,
                                      native_id=info['id'], underlying_id=source.get('underlying_ids',{}).get(info['id'], item_id),
                                      original_publication_basis='YouTube release/upload metadata'))
                            receipt.value['output_count'] += 1
                        except Exception as e:
                            receipt.error(f"{source['source_id']} item {entry.get('id')}: {e}")
                            failed = True
            except Exception as e:
                receipt.error(f"{source['source_id']}: {e}")
                failed = True
    return int(failed)


if __name__ == '__main__':
    main(execute)
