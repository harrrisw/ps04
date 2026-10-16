"""Explain inspectable changes using saved artifacts, never inferred execution history."""
from lib.common import digest, read_json, read_jsonl


def compare(previous,current):
    def rows(run,name):
        return read_jsonl(run/name) if (run/name).exists() else []
    old_items={r['item_id']:r for r in rows(previous,'eligible.jsonl')}
    new_items={r['item_id']:r for r in rows(current,'eligible.jsonl')}
    old_decisions={d['item_id']:d for d in rows(previous,'decisions.jsonl')}
    new_decisions={d['item_id']:d for d in rows(current,'decisions.jsonl')}
    changes=[]
    for key in sorted(old_decisions.keys() | new_decisions.keys()):
        before,after=old_decisions.get(key),new_decisions.get(key)
        if before!=after:
            changes.append(dict(item_id=key,title=(new_items.get(key) or old_items.get(key) or {}).get('title'),
                                before=before,after=after))
    def policy(run):
        p=run/'config/editorial_policy.md'
        return digest(p.read_text(encoding='utf-8')) if p.exists() else None
    old_briefs={b['piece_id']:b['argument'] for b in rows(previous,'briefs.jsonl')}
    new_briefs={b['piece_id']:b['argument'] for b in rows(current,'briefs.jsonl')}
    return dict(previous_run=previous.name,current_run=current.name,
        different_actual_dates=read_json(previous/'run.json')['as_of_date']!=read_json(current/'run.json')['as_of_date'],
        policy_changed=policy(previous)!=policy(current),
        newly_eligible=[dict(item_id=k,title=new_items[k]['title']) for k in sorted(new_items.keys()-old_items.keys())],
        no_longer_eligible=sorted(old_items.keys()-new_items.keys()),
        changed_versions=[k for k in new_items.keys() & old_items.keys() if new_items[k]['version_id']!=old_items[k]['version_id']],
        editorial_changes=changes,arguments_before=old_briefs,arguments_after=new_briefs,
        interpretation='Compare reasons and evidence directly. New discovery is not necessarily a newly published development; policy and source-list changes can also change selections.')


def markdown(result):
    lines=[f"# Run comparison: {result['previous_run']} → {result['current_run']}\n",
           f"Different actual UTC dates: **{result['different_actual_dates']}**. Policy changed: **{result['policy_changed']}**.\n",
           f"Newly eligible: {len(result['newly_eligible'])}; changed versions: {len(result['changed_versions'])}; no longer eligible: {len(result['no_longer_eligible'])}.\n",
           result['interpretation']+'\n','## Editorial decisions\n']
    for change in result['editorial_changes']:
        before=change['before'] or {}
        after=change['after'] or {}
        lines.append(f"### {change['title'] or change['item_id']}\n\n**Before:** {before.get('decision','no recorded decision')} — {before.get('reason','')}\n\n**After:** {after.get('decision','no recorded decision')} — {after.get('reason','')}\n")
    lines.append('## Arguments\n')
    for pid,arg in result['arguments_after'].items():
        lines.append(f"- {pid}: {arg}\n  Previous: {result['arguments_before'].get(pid,'No completed brief')}\n")
    return '\n'.join(lines)
