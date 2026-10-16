# MIT Parley setup

The active provider is configured in `config/project.json`:

```json
"ai": {
  "provider": "parley",
  "model": "gpt-5.4-mini"
}
```

Keep the other existing `ai` settings. On October 16, the authenticated MIT
`/v1/models` endpoint listed `gpt-5.4-mini`, while a live request using the
student's example alias `openai` returned HTTP 400 (unsupported model). The root
configuration now uses the supported model ID. The transport in `lib/parley.py` calls
`https://parley.api.mit.edu/v1/chat/completions` with a Bearer authorization header
and the documented `model` and `messages` fields. `lib/model.py` connects this
transport to all four editorial stages and validates generated JSON locally.

## Where to put your key

From PowerShell in this repository, run:

```powershell
.\scripts\set_parley_key.ps1
```

If PowerShell blocks scripts, use Git Bash instead:

```bash
bash scripts/share_parley_key.sh
bash run.sh
```

This Bash helper saves the key privately in the Git-ignored local handoff file
described below; it also allows this coding agent to run the pipeline.

Paste your real key at the hidden prompt. It sets `PARLEY_API_KEY` only for that
terminal session. No key is saved to the repository or typed into shell history.
The helper makes no API request. Use the same terminal for the subsequent run:

```powershell
& 'C:/Program Files/Git/bin/bash.exe' run.sh
```

You may instead supply `PARLEY_API_KEY` through your own environment-variable
manager. To explicitly share the key with an agent-run process that cannot inherit
your terminal environment, run `bash scripts/share_parley_key.sh`. That helper
stores it in `.secrets/parley_api_key.txt`, ignored by Git. Parley reads this file
only when `PARLEY_API_KEY` is absent; the key never enters configuration snapshots
or prompts. Delete that file when you no longer want to retain the local handoff.
`.env` files are ignored by Git but are **not automatically loaded**.
Never put the key in `config/project.json`: that file is copied into run artifacts
and included in model input. Clear the session key with:

```powershell
Remove-Item Env:PARLEY_API_KEY
```

## Credits, validation, and existing drafts

Parley API calls consume your MIT account's API credits. Check your account's
available credits and budget controls before a full run. This adapter does not
purchase credits, estimate prices, or enforce a dollar spending cap. The existing
`allow_paid_api: false` setting does not prevent Parley credit consumption; it does
not act as a budget control. No direct commercial API provider is configured.
Usage counts are retained when the API supplies them; unknown dollar costs stay
unknown. Failed requests are not retried automatically.

The adapter is tested with offline mocked responses. Authenticated model discovery
has also succeeded with the student's key. Full generation results are recorded
in the live run summaries and [validation record](VALIDATION.md). It uses prompt-based JSON
instructions and local schema validation because the supplied example does not
document a server-side structured-output option. Unsupported, incomplete, or
non-JSON responses fail visibly rather than being used as editorial evidence.

Existing October 10 drafts were generated with Codex. Their snapshots and AI
disclosures remain accurate. Changing the root provider applies to new runs;
resuming an old run uses its original provider snapshot. Run a new collection to
obtain a new, honestly dated Parley-generated series. The original deadline was
October 13; an October 15 or later run must not be described as a pre-deadline run.

Official references: [MIT access instructions](https://mitsloanedtech.mit.edu/tools/parley-api/)
and [MIT API documentation](https://parley-docs.mit.edu/) (MIT sign-in required).
The endpoint, Bearer header, and `openai` alias were supplied by the student from
their documentation on October 15, 2026.
