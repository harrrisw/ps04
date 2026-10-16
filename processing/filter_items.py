import sys
from lib.common import date_reason, emit, jsonl, main, read_json, run_dir, save_jsonl, stage, validate_item


def execute():
    run = run_dir()
    with stage(run, 'filter_items') as receipt:
        rows = jsonl(sys.stdin)
        receipt.value['input_count'] = len(rows)
        as_of = read_json(run / 'run.json')['as_of_date']
        excluded = []
        eligible = []
        for row in rows:
            validate_item(row)
            reason = date_reason(row['published_at'], as_of)
            if reason:
                excluded.append(dict(item_id=row['item_id'], version_id=row['version_id'], reason=reason,
                                     detail=f"published_at={row['published_at']!r}; inclusive 30 UTC dates ending {as_of}"))
            else:
                eligible.append(row)
        save_jsonl(run / 'exclusions.jsonl', excluded)
        for row in eligible:
            emit(row)
        receipt.value['output_count'] = len(eligible)


if __name__ == '__main__':
    main(execute)
