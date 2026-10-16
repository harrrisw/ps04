from collectors.feed_support import candidates
from lib.common import emit, main, read_json, run_dir, stage


def execute():
    run = run_dir()
    failed = False
    with stage(run, 'fetch_podcasts') as receipt:
        sources = [s for s in read_json(run / 'config/sources.json') if s['kind'] == 'podcast']
        receipt.value['input_count'] = len(sources)
        receipt.value['tools'].append('feedparser')
        for source in sources:
            try:
                for row in candidates(source):
                    if not row['media_url']:
                        raise RuntimeError(f"Episode lacks audio enclosure: {row['title']}")
                    emit(row)
                    receipt.value['output_count'] += 1
            except Exception as e:
                receipt.error(f"{source['source_id']}: {e}")
                failed = True
    return int(failed)


if __name__ == '__main__':
    main(execute)
