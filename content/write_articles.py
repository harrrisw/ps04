import sys
from content.support import brief_evidence, format_citations, source_notes
from lib.common import PIECES, atomic_text, emit, jsonl, main, rel, run_dir, stage
from lib.model import STRING, context, infer, obj


def execute():
    run = run_dir()
    with stage(run, 'write_articles') as receipt:
        briefs = jsonl(sys.stdin)
        if sorted(b['piece_id'] for b in briefs) != PIECES:
            raise ValueError('Expected three briefs with IDs 01, 02, 03')
        receipt.value['input_count'] = len(briefs)
        for brief in briefs:
            items = brief_evidence(run, brief)
            payload = context(run,items)
            payload.update(brief=brief, source_notes=source_notes(brief,items))
            result = infer(run,'article-'+brief['piece_id'],(run/'prompts/write_articles.md').read_text(encoding='utf-8'),
                           payload,obj(dict(markdown=STRING)),receipt)
            p = run/'articles'/(brief['piece_id']+'.md')
            atomic_text(p,format_citations(result['markdown'],items)+'\n')
            emit(dict(piece_id=brief['piece_id'],path=rel(p),claim_ids=[c['claim_id'] for c in brief['claims']]))
            receipt.value['output_count'] += 1


if __name__ == '__main__':
    main(execute)
