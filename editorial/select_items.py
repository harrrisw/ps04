import sys
from lib.common import emit, jsonl, main, read_json, run_dir, stage, validate_item
from lib.model import DECISION, array, context, infer, obj


def execute():
    run = run_dir()
    with stage(run, 'select_items') as receipt:
        rows = jsonl(sys.stdin)
        for row in rows:
            validate_item(row)
        receipt.value['input_count'] = len(rows)
        if not rows:
            raise RuntimeError('No eligible evidence to select')
        batch_size = read_json(run/'config/project.json').get('ai',{}).get('selection_batch_size',4)
        if not isinstance(batch_size,int) or batch_size < 1:
            raise ValueError('selection_batch_size must be positive')
        prompt = (run/'prompts/select_items.md').read_text(encoding='utf-8')
        all_decisions = []
        for offset in range(0,len(rows),batch_size):
            batch = rows[offset:offset+batch_size]
            result = infer(run, 'select_items', prompt, context(run,batch), obj(dict(decisions=array(DECISION))), receipt)
            expected = {(x['item_id'],x['version_id']) for x in batch}
            decisions = result['decisions']
            if len(decisions) != len(expected) or {(d['item_id'],d['version_id']) for d in decisions} != expected:
                raise ValueError('Model must return exactly one decision for every candidate version')
            for d in decisions:
                if not d['reason'].strip() or bool(d['piece_ids']) != (d['decision']=='accept'):
                    raise ValueError('Invalid decision reason or piece assignments')
            all_decisions.extend(decisions)
        for decision in all_decisions:
            emit(decision)
        receipt.value['output_count'] = len(all_decisions)


if __name__ == '__main__':
    main(execute)
