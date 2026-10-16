import re
from content.support import brief_evidence, source_notes
from lib.common import (PIECES, atomic_text, emit, iso_date, main, path, read_json, read_jsonl,
                        rel, run_dir, stage, write_json)
from review.check_content import assess


def execute():
    run = run_dir()
    with stage(run,'prepare_package') as receipt:
        current = assess(run)
        if not current['passed']:
            raise RuntimeError('Current content checks do not pass; repair errors before packaging')
        if not (run/'approval.json').exists():
            raise RuntimeError('Student approval is required. See docs/HUMAN_REVIEW.md.')
        approval = read_json(run/'approval.json')
        if approval.get('decision')!='approve' or approval.get('review_id')!=current['review_id']:
            raise RuntimeError('Human approval is absent, requests revision, or is stale')
        for key in ['reviewer','reviewed_at','notes']:
            if not isinstance(approval.get(key),str) or not approval[key].strip():
                raise ValueError('Approval requires '+key)
        iso_date(approval['reviewed_at'])
        folder = run/'package'
        folder.mkdir(parents=True,exist_ok=True)
        assets = []
        for name,kind in [('articles.jsonl','article'),('video_scripts.jsonl','video_script')]:
            for record in read_jsonl(run/name):
                content = path(record['path']).read_text(encoding='utf-8')
                # Keep readable citations, remove internal markers from audience-facing copies.
                content = re.sub(r'\s*\[claim:[^\]]+\]','',content)
                destination = folder / f"{record['piece_id']}-{kind}.md"
                atomic_text(destination,content)
                assets.append(dict(piece_id=record['piece_id'],kind=kind,path=rel(destination)))
        for brief in read_jsonl(run/'briefs.jsonl'):
            notes = source_notes(brief,brief_evidence(run,brief))
            destination = folder / f"{brief['piece_id']}-sources.md"
            atomic_text(destination,notes+'\n')
            assets.append(dict(piece_id=brief['piece_id'],kind='source_notes',path=rel(destination)))
        links = folder/'publication_links.json'
        if not links.exists():
            write_json(links,[dict(piece_id=pid,substack_url=None,youtube_url=None) for pid in PIECES])
        manual = ['Produce and review three 3–5 minute videos in Google Vids, including source cards and AI disclosure.',
                  'Publish three free-access Substack articles and three public/unlisted YouTube videos; cross-link each pair.',
                  'Add real publication URLs to publication_links.json; verify access while signed out.',
                  'Record the separate 4–6 minute technical demonstration and complete SUBMISSION.md.']
        manifest = dict(review_id=current['review_id'],assets=assets,manual_steps=manual,
                        publication_links_path=rel(links),status='ready_for_production')
        write_json(folder/'manifest.json',manifest)
        atomic_text(folder/'PRODUCTION.md','# Google Vids and publication handoff\n\n'+'\n'.join(f'{i+1}. {s}' for i,s in enumerate(manual))+'\n')
        receipt.value['input_count'] = 6
        receipt.value['output_count'] = len(assets)
        emit(manifest)


if __name__ == '__main__':
    main(execute)
