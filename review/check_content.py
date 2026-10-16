"""Mechanical evidence checks and a content fingerprint. Human judgment remains explicit."""
from collections import Counter
import re
from lib.common import (PIECES, coverage, date_reason, digest, emit, evidence_text, main, path,
                        read_json, read_jsonl, require_coverage, run_dir, stage, store_call)


def issue(artifact, explanation, severity='error'):
    return dict(artifact=artifact,severity=severity,explanation=explanation)


def validate_briefs(briefs, items, decisions):
    issues = []
    used = {}
    index = {(i['item_id'],i['version_id']):i for i in items}
    accepted = {(d['item_id'],d['version_id']):d for d in decisions if d.get('decision')=='accept'}
    if sorted(b.get('piece_id','') for b in briefs) != PIECES:
        issues.append(issue('briefs','Require exactly three briefs: 01, 02, 03'))
    if len({b.get('argument','').strip().lower() for b in briefs}) != 3:
        issues.append(issue('briefs','Central arguments must be distinct'))
    all_claims = set()
    for brief in briefs:
        pid = brief.get('piece_id','unknown')
        for field in ['title','question','argument','synthesis','limitations']:
            if not isinstance(brief.get(field),str) or not brief[field].strip():
                issues.append(issue(pid,'Missing ' + field))
        publishers = set()
        inference = False
        if not brief.get('claims'):
            issues.append(issue(pid,'No supported claims'))
        for claim in brief.get('claims',[]):
            cid = claim.get('claim_id','')
            if not cid.startswith(pid+'-') or cid in all_claims:
                issues.append(issue(pid,'Invalid or duplicated claim_id ' + cid))
            all_claims.add(cid)
            if claim.get('type') not in {'reported_fact','source_claim','inference'} or not claim.get('statement'):
                issues.append(issue(cid,'Invalid claim statement/type'))
            if not claim.get('evidence'):
                issues.append(issue(cid,'Claim has no evidence'))
            claim_publishers = set()
            for ref in claim.get('evidence',[]):
                key = (ref.get('item_id'),ref.get('version_id'))
                if key not in index or key not in accepted:
                    issues.append(issue(cid,'Reference is not an accepted eligible version: '+str(key)))
                    continue
                # Selection records intended pieces. Briefs record actual use, which
                # may change when a supported argument connects accepted sources.
                item = index[key]
                used[key] = item
                publishers.add(item['publisher_id'])
                claim_publishers.add(item['publisher_id'])
                try:
                    content = evidence_text(item)
                    locator = ref['locator']
                    if item['kind']=='feed':
                        quote = locator.get('quote')
                        if locator.get('type')!='text' or not quote or quote not in content['text']:
                            raise ValueError('Exact quoted passage does not occur in retained text')
                    else:
                        if locator.get('type')!='segment' or not content['segments']:
                            raise ValueError('Media reference requires a timestamped segment')
                        segments = content['segments']
                        ids = [s['segment_id'] for s in segments]
                        if len(ids)!=len(set(ids)):
                            raise ValueError('Duplicate transcript segment IDs')
                        selected = next((s for s in segments if s['segment_id']==locator.get('segment_id')),None)
                        if not selected or not (0 <= selected['start_seconds'] < selected['end_seconds']) or not selected['text'].strip():
                            raise ValueError('Missing or invalid transcript segment')
                except Exception as e:
                    issues.append(issue(cid,str(e)))
            if claim.get('type')=='inference' and len(claim_publishers)>=2:
                inference = True
        if len(publishers)<3:
            issues.append(issue(pid,'Each piece needs at least three independent publishers'))
        if not inference:
            issues.append(issue(pid,'Each piece needs an inference connecting at least two independent publishers'))
    if {r['kind'] for r in used.values()} != {'feed','youtube','podcast'}:
        issues.append(issue('series','All three input types must contribute to claims'))
    return issues, list(used.values())


def assess(run):
    meta = read_json(run/'run.json')
    issues = []
    fingerprint = {'as_of_date':meta['as_of_date'],'files':{},'evidence':{}}
    required = ['briefs.jsonl','decisions.jsonl','eligible.jsonl','articles.jsonl','video_scripts.jsonl']
    records = {}
    for filename in required:
        p = run/filename
        if not p.exists():
            issues.append(issue(filename,'Required artifact missing'))
            continue
        raw = p.read_text(encoding='utf-8-sig')
        fingerprint['files'][filename] = digest(raw)
        try:
            records[filename] = read_jsonl(p)
        except Exception as e:
            issues.append(issue(filename,str(e)))
    eligible = records.get('eligible.jsonl',[])
    try:
        require_coverage(eligible)
    except RuntimeError as e:
        issues.append(issue('eligible.jsonl',str(e)))
    seen_hash = {}
    seen_title = {}
    for item in eligible:
        reason = date_reason(item.get('published_at'),meta['as_of_date'])
        if reason:
            issues.append(issue(item['item_id'],'Evidence is ineligible: '+reason))
        try:
            ev = evidence_text(item)
            fingerprint['evidence'][item['item_id']+'@'+item['version_id']] = digest(ev)
            content_hash = item.get('content_hash') or digest(ev['text'])
            if item.get('content_hash') and item['content_hash'] != digest(re.sub(r'\s+',' ',ev['text']).strip().lower()):
                issues.append(issue(item['item_id'],'Retained text no longer matches its recorded content hash'))
            identity = item.get('underlying_id') or item['item_id']
            if content_hash in seen_hash and seen_hash[content_hash]!=identity:
                issues.append(issue(item['item_id'],'Identical content has unreconciled underlying identities'))
            seen_hash[content_hash] = identity
            normalized_title = re.sub(r'\W+','',item['title'].lower())
            title_key = (item['publisher_id'],normalized_title)
            if title_key in seen_title and seen_title[title_key]!=identity:
                issues.append(issue(item['item_id'],'Same producer/title may be a cross-post; reconcile underlying_id'))
            seen_title[title_key] = identity
        except Exception as e:
            issues.append(issue(item.get('item_id','evidence'),str(e)))
    decisions = records.get('decisions.jsonl',[])
    expected = {(r['item_id'],r['version_id']) for r in eligible}
    actual = [(r.get('item_id'),r.get('version_id')) for r in decisions]
    if set(actual)!=expected or len(actual)!=len(set(actual)):
        issues.append(issue('decisions.jsonl','Expected exactly one editorial decision per eligible version'))
    for d in decisions:
        if d.get('decision') not in {'accept','reject','defer'} or not d.get('reason'):
            issues.append(issue('decisions.jsonl','Invalid decision or missing reason'))
        if bool(d.get('piece_ids')) != (d.get('decision')=='accept'):
            issues.append(issue('decisions.jsonl','Invalid piece assignments'))
    briefs = records.get('briefs.jsonl',[])
    brief_issues, used = validate_briefs(briefs,eligible,decisions)
    issues.extend(brief_issues)
    for item in used:
        try:
            stored = store_call('get',item['item_id'],item['version_id'],run=run)[0]
            if any(stored.get(k)!=item.get(k) for k in ['text_path','segments_path','published_at','publisher_id','kind']):
                raise ValueError('Run evidence disagrees with stored version')
        except Exception as e:
            issues.append(issue(item['item_id'],str(e)))
    for manifest in ['articles.jsonl','video_scripts.jsonl']:
        rows = records.get(manifest,[])
        if sorted(r.get('piece_id','') for r in rows)!=PIECES:
            issues.append(issue(manifest,'Require exactly three content manifest records'))
        for row in rows:
            pid = row.get('piece_id')
            brief = next((b for b in briefs if b.get('piece_id')==pid),None)
            if not brief:
                continue
            claims = {c['claim_id'] for c in brief['claims']}
            if set(row.get('claim_ids',[]))!=claims:
                issues.append(issue(manifest+':'+str(pid),'Manifest does not cover the brief claims'))
            try:
                p = path(row['path'])
                if not p.is_relative_to(run.resolve()):
                    raise ValueError('Draft must be inside its run directory')
                text = p.read_text(encoding='utf-8')
                fingerprint['files'][row['path']] = digest(text)
                markers = set(re.findall(r'\[claim:([^\]]+)\]',text))
                if markers!=claims:
                    issues.append(issue(row['path'],'Claim markers missing or unknown; article/script consistency incomplete'))
                if meta['as_of_date'] not in text:
                    issues.append(issue(row['path'],'Missing actual run as-of date'))
                if not re.search(r'\[[^\]]+\]\(https?://',text):
                    issues.append(issue(row['path'],'No audience-readable source links'))
                for claim in brief['claims']:
                    for ref in claim['evidence']:
                        item = next((i for i in used if i['item_id']==ref['item_id'] and i['version_id']==ref['version_id']),None)
                        if item and item['url'] not in text and (not item.get('media_url') or item['media_url'] not in text):
                            issues.append(issue(row['path'],'Missing source link for '+item['item_id']))
                if manifest=='articles.jsonl':
                    body = re.split(r'(?im)^#{1,3}\s+references',text)[0]
                    count = len(re.findall(r"\b[\w'-]+\b",re.sub(r'\[claim:[^\]]+\]|\([^)]*https?[^)]*\)','',body)))
                    if not 600<=count<=900:
                        issues.append(issue(row['path'],f'Approximate article word count {count}; target 600–900','warning'))
                else:
                    narration = re.findall(r'\*\*Narration:\*\*(.*?)(?=\*\*Visual:|\n#{1,3} |\Z)',text,re.S)
                    count = len(' '.join(narration).split())
                    if not 390<=count<=750:
                        issues.append(issue(row['path'],f'Estimated spoken word count {count}; verify 3–5 minute duration','warning'))
            except Exception as e:
                issues.append(issue(row.get('path',manifest),str(e)))
    issues.append(issue('human_review','Verify semantic claim support, source independence, media quotations, original synthesis, missing perspectives, and article/script factual consistency. Markers alone do not prove these.','warning'))
    return dict(review_id=digest(fingerprint),passed=not any(i['severity']=='error' for i in issues),
                issues=issues,coverage=coverage(eligible),used_coverage=coverage(used),as_of_date=meta['as_of_date'])


def execute():
    run = run_dir()
    with stage(run,'check_content') as receipt:
        result = assess(run)
        receipt.value['input_count'] = len(result['issues'])
        receipt.value['output_count'] = 1
        emit(result)
    # A completed assessment exits zero even if it finds blocking errors.


if __name__ == '__main__':
    main(execute)
