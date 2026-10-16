"""MIT Parley transport; credentials stay outside configuration and run artifacts."""
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

ENDPOINT = 'https://parley.api.mit.edu/v1/chat/completions'
LOCAL_KEY_FILE = Path(__file__).resolve().parents[1] / '.secrets/parley_api_key.txt'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError('Parley redirected the request; verify the MIT endpoint before retrying')


def complete(model, prompt, timeout):
    key = os.environ.get('PARLEY_API_KEY', '').strip()
    if not key:
        # Explicit local handoff from the user's terminal; never copied into runs.
        secret = LOCAL_KEY_FILE
        if secret.is_file():
            key = secret.read_text(encoding='utf-8-sig').strip()
    if not key:
        raise RuntimeError('Set PARLEY_API_KEY or run bash scripts/share_parley_key.sh; see docs/PARLEY.md')
    if not isinstance(model, str) or not model.strip():
        raise ValueError('Set ai.model to a model alias from your MIT Parley documentation')
    # Use the request shape supplied from MIT documentation by the user. Do not
    # assume support for provider-specific schema, temperature, or token fields.
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(dict(model=model, messages=[dict(role='user', content=prompt)])).encode(),
        headers={'Authorization': 'Bearer '+key, 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            reply = json.load(response)
    except urllib.error.HTTPError as exc:
        # Error bodies and headers may contain secrets; never persist or echo them.
        hint = {400: 'check the model ID against the authenticated /v1/models endpoint and verify the request format',
                401: 'check the API key', 403: 'check account/model access',
                429: 'check your Parley quota or rate limit'}.get(exc.code, 'check the MIT API documentation')
        raise RuntimeError(f'Parley HTTP {exc.code}: {hint}; no automatic retry was made') from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('Parley connection failed or timed out; no automatic retry was made') from None
    except ValueError:
        raise RuntimeError('Parley returned a non-JSON HTTP response') from None
    try:
        choice = reply['choices'][0]
        if choice.get('finish_reason') not in (None, 'stop'):
            raise RuntimeError('Parley did not finish a usable answer; response was not accepted')
        content = choice['message']['content']
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError('Parley returned no text answer')
        # A plain JSON fence is harmless; other surrounding prose remains invalid.
        text = content.strip()
        if text.startswith('```json\n') and text.endswith('\n```'):
            text = text[8:-4].strip()
        result = json.loads(text)
    except (KeyError, IndexError, TypeError, ValueError):
        raise RuntimeError('Parley returned an unexpected response or invalid generated JSON') from None
    usage = reply.get('usage') or {}
    counts = {k: v for k, v in usage.items()
              if k in {'prompt_tokens', 'completion_tokens', 'total_tokens'}
              and isinstance(v, int) and not isinstance(v, bool) and v >= 0} if isinstance(usage, dict) else {}
    served_model = reply.get('model')
    return result, dict(model=served_model if isinstance(served_model, str) else None,
                        usage=counts, endpoint=ENDPOINT)
