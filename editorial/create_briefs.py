import sys
from lib.common import PIECES, emit, evidence_text, jsonl, main, read_jsonl, require_coverage, run_dir, save_jsonl, stage
from lib.model import BRIEF, STRING, array, context, infer, obj


def checked_briefs(run, prompt, payload, items, decisions, receipt):
    from review.check_content import validate_briefs
    schema = obj(dict(briefs=array(BRIEF), error=STRING))
    result = infer(run, 'create_briefs', prompt, payload, schema, receipt)
    briefs = result['briefs']
    if sorted(b['piece_id'] for b in briefs) != PIECES:
        raise RuntimeError('Model could not support three distinct briefs: ' + result['error'])
    issues, _ = validate_briefs(briefs, items, decisions)
    errors = [i for i in issues if i['severity'] == 'error']
    if errors:
        receipt.value['notes'].append('Initial brief validation failed; one evidence-grounded correction requested. Errors: '+str(errors))
        index = {(item['item_id'], item['version_id']): item for item in items}
        invalid_quotes = []
        for brief in briefs:
            for claim in brief['claims']:
                for ref in claim['evidence']:
                    item = index.get((ref['item_id'], ref['version_id']))
                    quote = ref['locator'].get('quote')
                    if item and item['kind'] == 'feed' and quote and quote not in evidence_text(item)['text']:
                        invalid_quotes.append(dict(claim_id=claim['claim_id'], reference=ref,
                            cited_title=item['title'], problem='This exact quote is NOT in this item. Remove this reference or replace it with a genuinely supporting exact passage from this item.'))
        repair = dict(payload, proposed_briefs=briefs, validation_errors=errors,
                      invalid_text_references=invalid_quotes)
        instruction = prompt + ('\n\nCorrect the proposed briefs using the supplied evidence and validation errors. '
            'For each text reference, copy a SHORT EXACT CONTIGUOUS passage from that referenced item, '
            'preserving punctuation and capitalization. Never borrow a quote from a different item. '
            'If a statement is unsupported, revise or remove it; do not invent a replacement quote. '
            'Preserve all coverage and independence requirements. Return the complete corrected briefs. '
            'This is the only correction attempt; if evidence is insufficient, return no briefs and explain why.')
        result = infer(run, 'create_briefs_repair', instruction, repair, schema, receipt)
        briefs = result['briefs']
        issues, _ = validate_briefs(briefs, items, decisions)
        errors = [i for i in issues if i['severity'] == 'error']
    if errors:
        raise ValueError('Invalid briefs after one correction attempt: ' + str(errors))
    return briefs


def execute():
    run = run_dir()
    with stage(run, 'create_briefs') as receipt:
        decisions = jsonl(sys.stdin)
        eligible = read_jsonl(run/'eligible.jsonl')
        require_coverage(eligible)
        selected = {(d['item_id'],d['version_id']) for d in decisions if d['decision']=='accept'}
        items = [r for r in eligible if (r['item_id'],r['version_id']) in selected]
        if len({r['publisher_id'] for r in items}) < 3 or {r['kind'] for r in items} != {'feed','youtube','podcast'}:
            raise RuntimeError('Accepted evidence lacks three publishers or all required input kinds')
        receipt.value['input_count'] = len(decisions)
        payload = context(run,items)
        payload['decisions'] = decisions
        briefs = checked_briefs(run,(run/'prompts/create_briefs.md').read_text(encoding='utf-8'),
                                payload,items,decisions,receipt)
        for brief in sorted(briefs,key=lambda b:b['piece_id']):
            for claim in brief['claims']:
                for e in claim['evidence']:
                    e['locator'] = {k:v for k,v in e['locator'].items() if v is not None}
            emit(brief)
        usage=[]
        for item in items:
            pieces=[b['piece_id'] for b in briefs if any(e['item_id']==item['item_id'] and e['version_id']==item['version_id']
                    for c in b['claims'] for e in c['evidence'])]
            usage.append(dict(item_id=item['item_id'],version_id=item['version_id'],piece_ids=pieces))
        save_jsonl(run/'usage.jsonl',usage)
        receipt.value['output_count'] = len(briefs)


if __name__ == '__main__':
    main(execute)
