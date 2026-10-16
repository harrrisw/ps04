"""I/O, receipts, and validation shared by independent pipeline components."""
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
UTC = dt.timezone.utc
KINDS = {'feed', 'youtube', 'podcast'}
PIECES = ['01', '02', '03']


def now():
    return dt.datetime.now(UTC).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def path(value):
    p = (ROOT / value).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError('Paths must remain inside the repository')
    return p


def rel(p):
    return Path(p).resolve().relative_to(ROOT).as_posix()


def read_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def write_json(p, value):
    atomic_text(p, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def atomic_text(p, text):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(text, encoding='utf-8', newline='\n')
    os.replace(tmp, p)


def jsonl(stream):
    rows = []
    for n, line in enumerate(stream, 1):
        if line.strip():
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError('record must be an object')
                rows.append(row)
            except (ValueError, TypeError) as e:
                raise ValueError(f'Malformed JSONL line {n}: {e}') from e
    return rows


def read_jsonl(p):
    with Path(p).open(encoding='utf-8-sig') as f:
        return jsonl(f)


def save_jsonl(p, rows):
    atomic_text(p, ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))


def emit(value):
    print(json.dumps(value, ensure_ascii=False))


def iso_date(value):
    if not isinstance(value, str):
        raise ValueError('date must be a string')
    d = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    return d.astimezone(UTC).date()


def date_reason(value, as_of):
    if value is None:
        return 'unknown_date'
    try:
        day = iso_date(value)
    except (ValueError, TypeError, OverflowError):
        return 'invalid_date'
    end = dt.date.fromisoformat(as_of)
    if day > end:
        return 'future_date'
    if day < end - dt.timedelta(days=29):
        return 'outside_window'
    return None


def validate_item(r, candidate=False):
    for k in ['item_id', 'source_id', 'publisher_id', 'kind', 'title', 'url', 'retrieved_at']:
        if not isinstance(r.get(k), str) or not r[k].strip():
            raise ValueError(f'Missing/non-string {k}')
    if r['kind'] not in KINDS:
        raise ValueError('Invalid kind')
    for k in ['published_at', 'media_url']:
        if k not in r or (r[k] is not None and not isinstance(r[k], str)):
            raise ValueError(f'Invalid {k}')
    if not candidate:
        for k in ['version_id', 'text_path']:
            if not isinstance(r.get(k), str) or not r[k]:
                raise ValueError(f'Invalid {k}')
        if 'segments_path' not in r:
            raise ValueError('Missing segments_path')


def run_dir():
    if len(sys.argv) != 2:
        raise ValueError('Expected RUN_DIR as the only argument')
    p = path(sys.argv[1])
    if not (p / 'run.json').is_file():
        raise ValueError('RUN_DIR must contain run.json')
    return p


class Receipt:
    def __init__(self, run, stage):
        self.run = Path(run)
        self.value = dict(stage=stage, status='running', input_count=0, output_count=0,
                          started_at=now(), finished_at=None, tools=['python'], models=[],
                          cost_usd=0, cost_is_estimate=False, errors=[], notes=[])
        self.clock = time.monotonic()

    def error(self, error):
        self.value['errors'].append(str(error))

    def finish(self, status=None):
        v = self.value
        v['status'] = status or ('incomplete' if v['errors'] else 'completed')
        v['finished_at'] = now()
        v['elapsed_seconds'] = round(time.monotonic() - self.clock, 3)
        write_json(self.run / 'logs' / f"{v['started_at'].replace(':', '')}-{v['stage']}-{uuid.uuid4().hex[:10]}.json", v)


@contextlib.contextmanager
def stage(run, name):
    r = Receipt(run, name)
    try:
        yield r
    except Exception as e:
        r.error(e)
        r.finish('failed')
        raise
    else:
        r.finish()


def main(fn):
    try:
        code = fn()
        sys.exit(code or 0)
    except (ValueError, KeyError, TypeError) as e:
        print(f'Invalid input: {e}', file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f'{type(e).__name__}: {e}', file=sys.stderr)
        sys.exit(1)


def store_call(*args, rows=None, run=None):
    # Cross-component store access always goes through the documented shell command.
    bash = os.environ.get('PIPELINE_BASH', 'bash')
    if os.name == 'nt' and bash == 'bash' and Path('C:/Program Files/Git/bin/bash.exe').exists():
        bash = 'C:/Program Files/Git/bin/bash.exe'
    env = dict(os.environ, PIPELINE_PYTHON=sys.executable)
    if run:
        env['PIPELINE_RUN_DIR'] = rel(run)
    p = subprocess.run([bash, 'data/store.sh', *args], cwd=ROOT, env=env, text=True,
                       encoding='utf-8', capture_output=True,
                       input=None if rows is None else ''.join(json.dumps(x) + '\n' for x in rows))
    if p.returncode:
        raise RuntimeError(p.stderr.strip() or 'Store command failed')
    return jsonl(p.stdout.splitlines())


def evidence_text(item):
    text = path(item['text_path']).read_text(encoding='utf-8')
    seg = read_json(path(item['segments_path'])) if item.get('segments_path') else None
    return dict(item=item, text=text, segments=seg)


def coverage(items):
    # underlying_id reconciles known cross-posts; text hash catches identical extracts.
    unique = {}
    for item in items:
        key = item.get('underlying_id') or item['item_id']
        unique.setdefault(key, item)
    rows = list(unique.values())
    return dict(distinct_items=len(rows), independent_publishers=len({r['publisher_id'] for r in rows}),
                by_kind={k: sum(r['kind'] == k for r in rows) for k in sorted(KINDS)},
                by_publisher={p: sum(r['publisher_id'] == p for r in rows)
                              for p in sorted({r['publisher_id'] for r in rows})},
                duplicate_observations=len(items)-len(rows))


def require_coverage(items):
    c = coverage(items)
    if c['distinct_items'] < 12 or c['independent_publishers'] < 6 or any(n < 2 for n in c['by_kind'].values()):
        raise RuntimeError('Insufficient evidence: need 12 distinct items, 6 independent publishers, '
                           f'and 2 of each kind; actual coverage: {json.dumps(c)}')
    return c
