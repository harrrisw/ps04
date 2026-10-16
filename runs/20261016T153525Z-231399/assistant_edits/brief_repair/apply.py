"""One-time assistant corrections; not student review or model-generated output."""
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from lib.common import atomic_text, evidence_text, read_json, read_jsonl, save_jsonl, stage, write_json
from review.check_content import validate_briefs

run = Path(__file__).resolve().parents[2]
folder = Path(__file__).parent
original = run/'ai_calls/create_briefs_repair-14f349c4de/response.json'
briefs = copy.deepcopy(read_json(original)['briefs'])
write_json(folder/'before.json', briefs)
items = read_jsonl(run/'eligible.jsonl')
decisions = read_jsonl(run/'decisions.jsonl')
claims = {c['claim_id']: c for b in briefs for c in b['claims']}
video = next(i for i in items if i['item_id']=='youtube:XCmsCJcD0Kw')

def segment(number):
    return dict(item_id=video['item_id'], version_id=video['version_id'],
                locator=dict(type='segment',segment_id=f's{number:05d}'))

claims['01-c1']['type'] = 'inference'
claims['01-c1']['statement'] = 'Crayon and NewMR describe source-connected workflows that small teams could investigate for retrieving and checking research context; these examples do not establish a market-wide shift or measured benefits.'
claims['01-c4']['evidence'] = [segment(35), segment(51), segment(52), claims['01-c4']['evidence'][1]]
claims['01-c4']['statement'] = 'An actionable pilot idea is to ask AI to gather context, report its sources and gaps, and retain links from findings to research material.'
claims['01-c5']['type'] = 'source_claim'
claims['01-c5']['statement'] = 'NewMR recommends asking AI to inspect relevant files, while Nielsen Norman Group argues that an assistant should retrieve information already available to it without requiring repeated manual pasting.'
claims['02-c2']['statement'] = 'Marketing AI Institute describes a second-agent review of flagged items and warns that multiple agents can agree on the same wrong answer; these passages do not establish measured time savings.'
claims['02-c4']['statement'] = 'Reported restrictions on Anthropic internal evaluations and the fact-checking workflow\u2019s retained editorial responsibility support testing human control in a pilot; neither establishes a general small-business failure rate.'
claims['02-c6']['statement'] = 'Crayon\u2019s source links and Nielsen Norman Group\u2019s emphasis on visible search coverage suggest useful pilot checks, while leaving small-business accuracy rates unestablished.'
claims['03-c1']['type'] = 'source_claim'
claims['03-c1']['statement'] = 'NewMR recommends beginning with drafting, extraction, or classification and avoiding automatic sending or deletion while learning; it also recommends narrowly defined triggers and checks.'
claims['03-c1']['evidence'] = [segment(n) for n in [136,137,138,139]]
claims['03-c2']['statement'] = 'Crayon\u2019s document-access controls and read-only API, alongside Vazen\u2019s account of bounded retail questions, suggest defining the question and accessible data before piloting a research tool; none independently proves accuracy or affordability.'
claims['03-c4']['statement'] = 'A pilot should distinguish retrieval quality from model capability and check organizational access rules; an example in another setting cannot establish the result for a small business.'
claims['03-c4']['evidence'][0]['locator']['quote'] = 'this comparison cannot separate the model\u2019s contribution from that of the retrieval system'
claims['03-c4']['evidence'] = claims['03-c4']['evidence'][:1] + [segment(126)]
claims['03-c5']['evidence'] = [claims['03-c5']['evidence'][0], segment(127), segment(129)]

with stage(run,'create_briefs') as receipt:
    receipt.value['tools'].append('assistant_editorial_correction')
    receipt.value['notes'].append('Assistant repaired invalid/misattributed citations and narrowed claims; source response preserved in '+str(original.relative_to(ROOT))+'. This is not an unattended model success or student approval. See assistant_edits/brief_repair/README.md.')
    issues, _ = validate_briefs(briefs,items,decisions)
    errors = [i for i in issues if i['severity']=='error']
    if errors:
        raise ValueError(errors)
    for b in briefs:
        for c in b['claims']:
            for ref in c['evidence']:
                ref['locator'] = {k:v for k,v in ref['locator'].items() if v is not None}
    save_jsonl(run/'briefs.jsonl',briefs)
    write_json(folder/'after.json',briefs)
    usage=[]
    accepted={(d['item_id'],d['version_id']) for d in decisions if d['decision']=='accept'}
    for item in items:
        if (item['item_id'],item['version_id']) in accepted:
            pieces=[b['piece_id'] for b in briefs if any(ref['item_id']==item['item_id'] for c in b['claims'] for ref in c['evidence'])]
            usage.append(dict(item_id=item['item_id'],version_id=item['version_id'],piece_ids=pieces))
    save_jsonl(run/'usage.jsonl',usage)
    receipt.value['input_count']=3
    receipt.value['output_count']=3

atomic_text(folder/'README.md', '''# Assistant brief corrections — October 16, 2026

Parley generated briefs with misattributed and inexact quotations. Its bounded
correction still left three invalid references. `before.json` preserves that
response; `after.json` and `apply.py` record the assistant's explicit corrections.
Original API responses and failed-stage receipts remain unchanged.

- 03-c1: the drafting/sending/deleting guidance belongs to NewMR, not the NN/g
  study guide. Replaced the references with retained segments s00136–s00139 and
  attributed the recommendation rather than asserting it is the safest method.
- 03-c4: corrected “the comparison” to the source's exact “this comparison”; used
  NewMR s00126 for organizational access rules and removed the unrelated disclosure
  reference. Narrowed the statement to match those passages.
- 03-c5: removed a quote incorrectly assigned to NN/g's study guide. It occurs in
  NewMR s00127; s00129 supports checking gaps and uncertainty.
- 01-c4: replaced a garbled automatic-transcription segment with clearer retained
  segments s00035, s00051, and s00052. No transcript text was rewritten.
- 01-c1/01-c5, 02-c2/02-c4/02-c6, and 03-c2: narrowed generalizations, removed an
  unsupported speed implication, and made attribution and transfer limits clear.

Every reference was rechecked mechanically against the immutable evidence. The
assistant inspected the retained text, not the original audio. Student audio/source
verification and final editorial approval remain pending. This is documented
assisted recovery, not a successful unattended briefing run.
''')
print('Corrected briefs pass evidence validation; ready for article/script generation.')
