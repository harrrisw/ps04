"""Entry-point metadata and receipts; no collection or editorial implementation."""
import datetime as dt
import os
import shutil
import sys
import uuid
from lib.common import ROOT, UTC, Receipt, emit, main, now, path, read_json, rel, write_json


def execute():
    if len(sys.argv) < 2:
        raise ValueError('Expected init or receipt')
    if sys.argv[1] == 'init':
        project = read_json(ROOT / 'config/project.json')
        for key in ['publication_name', 'topic', 'audience', 'central_question']:
            if not isinstance(project.get(key), str) or not project[key].strip():
                raise ValueError(f'config/project.json: {key} is required')
        sources = read_json(ROOT / 'config/sources.json')
        if not isinstance(sources, list) or not sources:
            raise ValueError('Configure sources before starting a live run')
        ids = set()
        for s in sources:
            for key in ['source_id', 'publisher_id', 'kind', 'url']:
                if not isinstance(s.get(key), str) or not s[key]:
                    raise ValueError(f'Source requires {key}')
            if s['kind'] not in {'feed','youtube','podcast'} or s['source_id'] in ids:
                raise ValueError('Invalid source kind or duplicate source_id')
            ids.add(s['source_id'])
        started = dt.datetime.now(UTC)
        run_id = started.strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:6]
        prior = sorted((ROOT / 'runs').glob('*/run.json'))
        previous = next((read_json(p)['run_id'] for p in reversed(prior)
                         if read_json(p).get('mode') == 'live'), None)
        run = ROOT / 'runs' / run_id
        run.mkdir(parents=True)
        shutil.copytree(ROOT / 'config', run / 'config')
        shutil.copytree(ROOT / 'prompts', run / 'prompts')
        overrides = {}
        if os.environ.get('PIPELINE_AI_PROVIDER'):
            provider = os.environ['PIPELINE_AI_PROVIDER']
            if provider not in {'codex', 'parley', 'ollama'}:
                raise ValueError('PIPELINE_AI_PROVIDER must be codex, parley, or ollama')
            overrides = {'provider': provider, 'model': os.environ.get('PIPELINE_AI_MODEL')}
            project.setdefault('ai', {}).update(overrides)
            write_json(run/'config/project.json', project)
        write_json(run / 'run.json', dict(run_id=run_id, started_at=started.isoformat().replace('+00:00','Z'),
                   as_of_date=started.date().isoformat(), mode='live', previous_run_id=previous,
                   ai_overrides=overrides))
        print(rel(run))
    elif sys.argv[1] == 'receipt' and len(sys.argv) == 6:
        run = path(sys.argv[2])
        r = Receipt(run, sys.argv[3])
        r.value['started_at'] = sys.argv[4]
        r.value['tools'] = ['bash']
        r.value['aggregation_only'] = True
        r.value['input_count'] = None
        r.value['output_count'] = None
        if sys.argv[5] != '0':
            r.error('One or more child stages failed; inspect their receipts')
        r.finish()
    else:
        raise ValueError('Invalid lifecycle command')


if __name__ == '__main__':
    main(execute)
