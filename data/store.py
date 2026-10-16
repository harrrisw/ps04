"""The sole owner of the persistent SQLite evidence index."""
import json
import os
import sqlite3
import sys
from lib.common import ROOT, Receipt, emit, jsonl, main, now, path, read_json, validate_item


def execute():
    args = sys.argv[1:]
    if not args or args[0] not in {'init','upsert','list','get'}:
        raise ValueError('Usage: store.sh init | upsert RUN_DIR | list | get ITEM_ID [VERSION_ID]')
    cmd = args[0]
    if (cmd in {'init','list'} and len(args) != 1) or (cmd == 'upsert' and len(args) != 2) or (cmd == 'get' and len(args) not in {2,3}):
        raise ValueError('Invalid store arguments')
    # An isolated repository copy is used for tests; no configurable external database.
    folder = ROOT / 'data/evidence'
    folder.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(folder / 'index.sqlite3', timeout=30)
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
      CREATE TABLE IF NOT EXISTS versions (
        item_id TEXT NOT NULL, version_id TEXT NOT NULL, record TEXT NOT NULL,
        created_at TEXT NOT NULL, PRIMARY KEY (item_id,version_id));
      CREATE TABLE IF NOT EXISTS latest (
        item_id TEXT PRIMARY KEY, version_id TEXT NOT NULL,
        FOREIGN KEY(item_id,version_id) REFERENCES versions(item_id,version_id));
      CREATE TABLE IF NOT EXISTS observations (
        id INTEGER PRIMARY KEY, item_id TEXT NOT NULL, version_id TEXT NOT NULL,
        run_id TEXT NOT NULL, retrieved_at TEXT NOT NULL, change TEXT NOT NULL);
    ''')
    target = args[1] if cmd == 'upsert' else os.environ.get('PIPELINE_RUN_DIR')
    # Standalone store operations also retain uniquely named receipts.
    run = path(target) if target else ROOT / 'runs/store-operations'
    receipt = Receipt(run, 'store_' + cmd)
    try:
        if cmd == 'upsert':
            meta = read_json(run / 'run.json')
            rows = jsonl(sys.stdin)
            for row in rows:
                validate_item(row)
            receipt.value['input_count'] = len(rows)
            changes = []
            observed = set()
            with db:
                for row in rows:
                    key = (row['item_id'], row['version_id'])
                    old = db.execute('SELECT version_id FROM latest WHERE item_id=?', (key[0],)).fetchone()
                    existing = db.execute('SELECT record FROM versions WHERE item_id=? AND version_id=?', key).fetchone()
                    if existing:
                        prior = json.loads(existing[0])
                        # Retrieval timestamps may change, but an ID cannot represent two different versions.
                        stable = ['title','url','published_at','publisher_id','kind','text_path','segments_path']
                        if any(prior.get(k) != row.get(k) for k in stable):
                            raise ValueError(f'Conflicting content for existing version {key}')
                    repeated = key in observed
                    change = 'unchanged' if repeated else ('new' if old is None else ('unchanged' if old[0] == key[1] else 'changed'))
                    db.execute('INSERT OR IGNORE INTO versions VALUES (?,?,?,?)',
                               (*key, json.dumps(row, ensure_ascii=False), now()))
                    if not repeated:
                        db.execute('INSERT INTO latest VALUES (?,?) ON CONFLICT(item_id) DO UPDATE SET version_id=excluded.version_id', key)
                    observed.add(key)
                    db.execute('INSERT INTO observations(item_id,version_id,run_id,retrieved_at,change) VALUES (?,?,?,?,?)',
                               (*key, meta['run_id'], row['retrieved_at'], change))
                    changes.append(dict(item_id=key[0], version_id=key[1], change=change))
            for record in changes:
                emit(record)
            receipt.value['output_count'] = len(changes)
        elif cmd == 'list':
            rows = db.execute('SELECT v.record FROM latest l JOIN versions v USING(item_id,version_id) ORDER BY item_id')
            for row in rows:
                emit(json.loads(row[0]))
                receipt.value['output_count'] += 1
        elif cmd == 'get':
            if len(args) == 3:
                row = db.execute('SELECT record FROM versions WHERE item_id=? AND version_id=?', tuple(args[1:])).fetchone()
            else:
                row = db.execute('SELECT v.record FROM latest l JOIN versions v USING(item_id,version_id) WHERE item_id=?', (args[1],)).fetchone()
            if row is None:
                raise RuntimeError('Evidence item/version not found')
            emit(json.loads(row[0]))
            receipt.value['output_count'] = 1
    except Exception as e:
        receipt.error(e)
        receipt.finish('failed')
        raise
    else:
        receipt.finish()
    finally:
        db.close()


if __name__ == '__main__':
    main(execute)
