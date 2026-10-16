"""JSON-only inference transport; all editorial decisions belong to their stages."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib
import urllib.request
import uuid
from lib.common import ROOT, atomic_text, digest, read_json, write_json


def infer(run, name, instruction, payload, schema, receipt):
    settings = read_json(run / 'config/project.json').get('ai', {})
    provider = settings.get('provider', 'codex')
    call = run / 'ai_calls' / (name + '-' + uuid.uuid4().hex[:10])
    call.mkdir(parents=True)
    prompt = instruction + '\n\nReturn only JSON matching this schema:\n' + json.dumps(schema) + '\n\nINPUT DATA:\n' + json.dumps(payload, ensure_ascii=False)
    atomic_text(call / 'prompt.txt', prompt)
    write_json(call / 'schema.json', schema)
    # No credentials, auth files, or environment snapshots are written to artifacts.
    receipt.value['tools'].append(provider)
    model = settings.get('model')
    if provider == 'codex' and not model:
        # Read only the configured model name; never inspect or copy auth credentials.
        config_home = Path(os.environ.get('CODEX_HOME') or (Path.home()/'.codex'))
        try:
            model = tomllib.loads((config_home/'config.toml').read_text(encoding='utf-8')).get('model')
        except (OSError,ValueError):
            pass
    receipt.value['models'].append(model or 'provider default (model ID not reported)')
    timeout = settings.get('timeout_seconds', 600)
    # Revalidate exact saved responses on a stage retry; do not spend account usage
    # regenerating an unchanged request after a downstream implementation repair.
    from jsonschema import validate
    for prior in sorted((run/'ai_calls').glob(name+'-*'),reverse=True):
        if prior==call or not (prior/'metadata.json').exists() or not (prior/'response.json').exists():
            continue
        metadata=read_json(prior/'metadata.json')
        if metadata.get('provider')!=provider or metadata.get('model')!=model:
            continue
        if (prior/'prompt.txt').read_text(encoding='utf-8')!=prompt:
            continue
        result=read_json(prior/'response.json')
        validate(result,schema)
        write_json(call/'response.json',result)
        write_json(call/'metadata.json',dict(provider=provider,model=model,prompt_sha256=digest(prompt),
                   cost_usd=0,reused_from=prior.relative_to(ROOT).as_posix()))
        receipt.value['notes'].append('Reused exact saved model response: '+prior.relative_to(ROOT).as_posix())
        return result
    print(f'AI {provider}/{model or "default"}: {name}',file=sys.stderr,flush=True)
    if provider == 'codex':
        executable = os.environ.get('CODEX_BIN') or shutil.which('codex')
        if not executable:
            raise RuntimeError('Codex CLI unavailable. Set CODEX_BIN or choose a local Ollama model.')
        login = subprocess.run([executable, 'login', 'status'], capture_output=True, text=True, encoding='utf-8')
        if login.returncode or 'chatgpt' not in (login.stdout + login.stderr).lower():
            raise RuntimeError('A ChatGPT Codex login is required. Paid API authentication is disabled for this project.')
        command = [executable, 'exec', '--sandbox', 'read-only', '--ephemeral', '--json',
                   '--output-schema', str(call / 'schema.json'), '--output-last-message', str(call / 'response.json')]
        if model:
            command.extend(['--model', model])
        command.append('-')
        receipt.value['cost_usd']=None
        proc = subprocess.run(command, cwd=ROOT, input=prompt, capture_output=True,
                              text=True, encoding='utf-8', errors='replace', timeout=timeout)
        atomic_text(call / 'events.jsonl', proc.stdout)
        atomic_text(call / 'stderr.txt', proc.stderr)
        if proc.returncode:
            raise RuntimeError(f'Codex exited {proc.returncode}; inspect {call.relative_to(ROOT)}')
        for line in proc.stdout.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get('type') == 'turn.completed':
                receipt.value.setdefault('usage', []).append(event.get('usage', {}))
        result = read_json(call / 'response.json')
    elif provider == 'parley':
        from lib.parley import complete
        receipt.value['cost_usd'] = None
        result, details = complete(model, prompt, timeout)
        validate(result, schema)
        write_json(call / 'response.json', result)
        write_json(call / 'api_usage.json', details)
        receipt.value.setdefault('usage', []).append(details['usage'])
        if details['model']:
            receipt.value['models'].append(details['model'])
        receipt.value['notes'].append('MIT Parley account credits; dollar cost not reported. No automatic retries.')
    elif provider == 'ollama':
        model = settings.get('model')
        if not model:
            raise ValueError('Set ai.model to an installed local Ollama model')
        # Local-only endpoint prevents accidentally routing to a billed hosted service.
        body = dict(model=model, prompt=prompt, stream=False, format=schema)
        req = urllib.request.Request('http://127.0.0.1:11434/api/generate', data=json.dumps(body).encode(),
                                     headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            reply = json.load(response)
        result = json.loads(reply['response'])
        write_json(call / 'response.json', result)
        receipt.value['cost_usd'] = 0
        receipt.value['notes'].append('Local inference; electricity/hardware cost not estimated')
    else:
        raise ValueError('Supported providers: codex (ChatGPT login), parley (MIT API key), ollama (local).')
    # Validation occurs before any generated record is published as a stage artifact.
    validate(result, schema)
    write_json(call / 'metadata.json', dict(provider=provider, model=model,
               prompt_sha256=digest(prompt), cost_usd=receipt.value['cost_usd']))
    return result


def obj(properties):
    return dict(type='object', properties=properties, required=list(properties), additionalProperties=False)


STRING = {'type':'string'}
def array(items):
    return {'type':'array','items':items}


DECISION = obj(dict(item_id=STRING, version_id=STRING, decision={'type':'string','enum':['accept','reject','defer']},
                    reason=STRING, piece_ids=array({'type':'string','enum':['01','02','03']})))
# Both locator fields are present in schema; the unused field is null and removed before emission.
LOCATOR = obj(dict(type={'type':'string','enum':['text','segment']},
                   quote={'type':['string','null']}, segment_id={'type':['string','null']}))
EVIDENCE = obj(dict(item_id=STRING, version_id=STRING, locator=LOCATOR))
CLAIM = obj(dict(claim_id=STRING, statement=STRING, type={'type':'string','enum':['reported_fact','source_claim','inference']},
                 evidence=array(EVIDENCE)))
BRIEF = obj(dict(piece_id={'type':'string','enum':['01','02','03']}, title=STRING, question=STRING,
                 argument=STRING, synthesis=STRING, limitations=STRING, claims=array(CLAIM)))


def context(run, items):
    from lib.common import evidence_text
    project = read_json(run / 'config/project.json')
    limit = project.get('ai',{}).get('max_evidence_chars_per_item',16000)
    sources = []
    for item in items:
        evidence = evidence_text(item)
        text = evidence['text']
        evidence['text'] = text[:limit]
        if evidence['segments']:
            count = 0
            selected = []
            for segment in evidence['segments']:
                if count + len(segment['text']) > limit:
                    break
                selected.append(segment)
                count += len(segment['text'])
            evidence['segments'] = selected
        evidence['excerpt_truncated'] = len(text) > limit
        sources.append(evidence)
    return dict(project=project, as_of_date=read_json(run/'run.json')['as_of_date'],
                policy=(run/'config/editorial_policy.md').read_text(encoding='utf-8'), evidence=sources)
