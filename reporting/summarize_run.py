import datetime as dt
from lib.common import ROOT, UTC, atomic_text, coverage, emit, main, now, read_json, read_jsonl, rel, run_dir, stage, write_json


def summarize(run):
    meta = read_json(run/'run.json')
    def rows(name):
        return read_jsonl(run/name) if (run/name).exists() else None
    candidates,items,eligible,decisions,changes = [rows(n) for n in
        ['candidates.jsonl','items.jsonl','eligible.jsonl','decisions.jsonl','changes.jsonl']]
    exclusions,early = rows('exclusions.jsonl'), rows('candidate_exclusions.jsonl')
    counts = dict(discovered=None if candidates is None else len(candidates),
                  extracted=None if items is None else len(items),
                  eligible=None if eligible is None else len(eligible),
                  excluded=None if exclusions is None else len(exclusions)+(len(early) if early else 0))
    for key in ['new','changed','unchanged']:
        counts[key] = None if changes is None else sum(r['change']==key for r in changes)
    for key in ['accepted','rejected','deferred']:
        label = {'accepted':'accept','rejected':'reject','deferred':'defer'}[key]
        counts[key] = None if decisions is None else sum(r['decision']==label for r in decisions)
    for key,filename in [('articles','articles.jsonl'),('video_scripts','video_scripts.jsonl')]:
        data = rows(filename)
        counts[key] = None if data is None else len(data)
    receipts = [read_json(p) for p in sorted((run/'logs').glob('*.json'))]
    latest = {}
    for r in receipts:
        key = r['stage']
        if key not in latest or r['finished_at']>=latest[key]['finished_at']:
            latest[key]=r
    incomplete = [dict(stage=r['stage'],status=r['status'],errors=r.get('errors',[])) for r in latest.values()
                  if r['status'] in {'incomplete','failed'} and not r.get('aggregation_only')]
    review = read_json(run/'review.json') if (run/'review.json').exists() else None
    status = 'awaiting_review' if review and review['passed'] else 'failed'
    package = read_json(run/'package/manifest.json') if (run/'package/manifest.json').exists() else None
    if status=='awaiting_review' and package and package.get('review_id')==review['review_id']:
        approval = read_json(run/'approval.json') if (run/'approval.json').exists() else {}
        if approval.get('decision')=='approve' and approval.get('review_id')==review['review_id']:
            status='ready_for_production'
    leaf = [r for r in receipts if not r.get('aggregation_only')]
    known = sum(r['cost_usd'] for r in leaf if r.get('cost_usd') is not None)
    unknown = [r['stage'] for r in leaf if r.get('cost_usd') is None]
    links = read_json(run/'package/publication_links.json') if (run/'package/publication_links.json').exists() else None
    started = dt.datetime.fromisoformat(meta['started_at'].replace('Z','+00:00'))
    completed = max((r['finished_at'] for r in receipts),default=meta['started_at'])
    end = dt.datetime.fromisoformat(completed.replace('Z','+00:00'))
    collection_stages = {'fetch_feeds','fetch_youtube','fetch_podcasts','extract_content'}
    collection_complete = (not any(r['stage'] in collection_stages for r in incomplete)
                           if collection_stages.issubset(latest) else None)
    active_seconds=sum(r.get('elapsed_seconds',0) for r in leaf
                       if r['stage'] not in {'store_get','store_list','summarize_run'})
    return dict(run_id=meta['run_id'],mode=meta['mode'],as_of_date=meta['as_of_date'],status=status,counts=counts,
                source_coverage=coverage(eligible or []),discovery_coverage=coverage(candidates or []),
                failed_or_incomplete_stages=incomplete,collection_complete=collection_complete,
                elapsed_seconds=round(active_seconds,3),
                elapsed_time_basis='Summed active stage durations, excluding nested store reads and summaries; includes retries',
                wall_span_seconds=round((end-started).total_seconds(),3),
                summed_stage_seconds=round(sum(r.get('elapsed_seconds',0) for r in leaf),3),
                time_since_start_seconds=round((dt.datetime.now(UTC)-started).total_seconds(),3),
                tools=sorted({t for r in leaf for t in r.get('tools',[])}),
                models=sorted({m for r in leaf for m in r.get('models',[])}),
                known_cost_usd=known,approximate_total_cost_usd=None if unknown else known,
                unknown_cost_stages=unknown,cost_is_estimate=any(r.get('cost_is_estimate',False) for r in leaf),
                remaining_manual_actions=['Verify sources and media passages, review policy/run comparison, and record final approval',
                    'Check actual run dates against the assignment-week requirement; later runs do not establish on-time completion',
                    'Google Vids production, Substack and YouTube publishing, technical demo, and submission'],
                publication_links=links,generated_at=now())


def execute():
    run = run_dir()
    with stage(run,'summarize_run') as receipt:
        result = summarize(run)
        previous = read_json(run/'run.json').get('previous_run_id')
        if previous and (ROOT/'runs'/previous/'run.json').exists():
            from reporting.compare_runs import compare, markdown
            comparison=compare(ROOT/'runs'/previous,run)
            write_json(run/'comparison.json',comparison)
            atomic_text(run/'comparison.md',markdown(comparison))
            result['comparison_path']=rel(run/'comparison.md')
        receipt.value['output_count']=1
        emit(result)


if __name__ == '__main__':
    main(execute)
