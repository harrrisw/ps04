# Setup and operation

This project prioritizes existing account access and free local software. The
current default is MIT Parley; [set your API key using these instructions](PARLEY.md).
Parley consumes MIT account credits. Codex with an existing ChatGPT login and local
Ollama are alternatives. Unreported dollar costs are unknown, not assumed zero.

## This Windows workspace

Git Bash is installed at `C:/Program Files/Git/bin/bash.exe`. The system `bash.exe`
points to WSL, which is not configured for this task. Portable Python 3.12.10 and
libraries are in the ignored `.tools/python/` directory; they are not part of Git.
Run in PowerShell from this repository:

```powershell
.\scripts\set_parley_key.ps1
& 'C:/Program Files/Git/bin/bash.exe' run.sh
& .tools/python/python.exe tests/test_pipeline.py
```

The required `bash run.sh` command works in Git Bash. The Bash runtime helper
automatically finds the portable Python, or uses Python on PATH elsewhere.
`PIPELINE_PYTHON` can select a specific interpreter. `CODEX_BIN` can select the
Codex CLI executable when it is not on PATH. Use `codex login status` to check login;
the Codex provider refuses API-key authentication. The separate Parley provider
uses `PARLEY_API_KEY`. Never copy credentials into tracked project files.

## Another machine

Install Git Bash (Windows) or Bash (Linux/macOS) and Python 3.11+. Supply
`PARLEY_API_KEY` in your environment. For the optional Codex provider instead,
install its CLI, set `ai.provider` to `codex` and `ai.model` to null, and use your
existing ChatGPT login. From the repository root:

```bash
python -m venv .venv
# Windows Git Bash:
source .venv/Scripts/activate
# Linux/macOS instead: source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-media.txt
export PIPELINE_PYTHON="$(command -v python)"
python tests/test_pipeline.py
bash run.sh
```

Local transcription uses faster-whisper's `base.en` model on CPU, downloading its
weights to `.tools/models/` on first use. It uses local compute, not a billed speech
API. The media requirements pin PyAV because a newer version removed an argument
used by faster-whisper. The default `youtube_transcript_mode: "local"` downloads
audio and transcribes it locally, avoiding the subtitle endpoint that returned
HTTP 429. Set `prefer_captions` to opt back into caption retrieval. The core
requirements install yt-dlp with curl-cffi impersonation support, matching EJS challenge scripts and Deno
runtime. Both YouTube discovery and audio extraction explicitly locate the Deno
executable, including when the portable Python Scripts folder is absent from PATH.
A PATH-installed Deno or Node is a fallback; yt-dlp checks runtime compatibility.
The media requirements install an FFmpeg binary through imageio-ffmpeg; extraction
finds it explicitly to repair DASH audio containers. Collection failures remain visible.

If an older environment reports `No supported JavaScript runtime`, update the
dependencies in Git Bash from this repository:

```bash
./.tools/python/python.exe -m pip install -r requirements.txt -r requirements-media.txt
```

On another Python setup, substitute the interpreter selected by `PIPELINE_PYTHON`.
No API key or Parley credits are involved in this dependency installation.
See the [official yt-dlp runtime guide](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

Three narrated local MP4 review copies and their reproduction commands are linked
in [VIDEO_REVIEW.md](VIDEO_REVIEW.md). Their renderer additionally requires
`requirements-video.txt` and Windows SAPI. Google Vids/HeyGen production remains
a separate step.

Optional local inference: install and start Ollama yourself, load a model suited
to structured research, and set `ai.provider` to `ollama` and `ai.model` to its
installed name in `config/project.json`. The endpoint is local-only. Output still
must pass the same JSON and evidence checks; model quality is not guaranteed.

## Configuration and artifacts

- `config/project.json`: audience, scope, voice, AI provider, extraction limits.
- `config/sources.json`: discovery endpoints, independent producer IDs, perspectives.
- `config/editorial_policy.md` and `prompts/`: editorial instructions.
- `config/evidence_overrides.json`: documented metadata corrections or known
  cross-post identities, keyed by item ID. Each entry requires a `reason`. Supported
  fields: `underlying_id`, `published_at`, `transcript_url`, `transcript_type`.

Each live run snapshots all configuration and prompts. Do not edit historical
snapshots to disguise a change. Change the root configuration and create a new run.
`ai_calls/` retains exact prompts, schemas, responses, and usage events.
An exact response from the same run and resolved model can be reused on a stage
retry; the new call metadata records `reused_from`. Changed requests are not cached.
If generated briefs fail evidence validation, the briefing stage requests one
correction with the exact invalid references and validates again. Both responses
and the errors remain recorded. This is an additional model call; invalid results
after correction stop the stage. Transport errors are not automatically retried.

`data/evidence/index.sqlite3` is the local persistent index, accessed only through
`data/store.sh`. It is ignored by Git; run records can reconstruct it. Original
downloads live in `data/media/` (ignored because of size), and immutable extracted
text/transcripts live in `data/assets/`. Commit the retained text/transcripts and
run artifacts needed to inspect the work. Source provenance includes download URLs;
YouTube media can be retrieved with yt-dlp from the retained canonical URL, and
podcast enclosures can be downloaded from `media_url`.

Version IDs hash sorted compact JSON of title, URL, original publication date,
publisher, input kind, underlying identity, extracted text, and segments. Retrieval
time does not change a version. Feed HTML is fetched again; identical extracted
content produces the same evidence version. Saved media is reused when identity
and metadata match; set `collection.refresh_media` true to explicitly check for
in-place media edits. This cache limitation is reported, not a claim that media
cannot have changed.

To reconstruct a fresh index from retained **live** runs:

```bash
bash scripts/restore_evidence.sh
```

## Review, replay, and packaging

Run commands from the root; replace `runs/RUN_ID` with an actual run. Individual
components use the interfaces in [ARCHITECTURE.md](../ARCHITECTURE.md).

```bash
bash data/store.sh list | bash processing/filter_items.sh runs/RUN_ID
bash review/check_content.sh runs/RUN_ID > runs/RUN_ID/review.json
python tools/review_sample.py runs/RUN_ID
```

After repairing a generation/check implementation, resume from saved decisions:

```bash
bash scripts/resume_drafts.sh runs/RUN_ID
```

If you have explicitly corrected and validated saved briefs, preserve those
corrections while regenerating only articles and scripts:

```bash
bash scripts/resume_drafts.sh runs/RUN_ID --keep-briefs
```

Record the original briefs, corrections, evidence, and author of the changes.
This is assisted recovery, not an unattended briefing success. Final content and
evidence checks still run, and no approval is created by either resume command.

This archives existing content/manifests and checks under `stage_history/`, then
retries briefing and generation without recollecting sources. It is not a new live
collection or a different-day run. Briefs may revise the selection stage's intended
piece assignments; `usage.jsonl` records actual source use in the resulting briefs.

The student completes the review sample and final approval as described in
[HUMAN_REVIEW.md](HUMAN_REVIEW.md). Then:

```bash
bash run.sh --package runs/RUN_ID
```

Packaging checks the current content and matching approval, writes audience-facing
copies and source notes, and preserves already entered publication links. It does
not recollect, regenerate, render videos, or publish. See [PRODUCTION.md](PRODUCTION.md).

Run again on a genuinely different UTC date. Preserve both runs; the inclusive
freshness window is the actual UTC date minus 29 days through that date. No flag
backdates a live run. See [DEMONSTRATION.md](DEMONSTRATION.md) for the remaining
assignment evidence.

Official implementation references:
[Codex non-interactive mode](https://developers.openai.com/codex/noninteractive/),
[Codex authentication](https://developers.openai.com/codex/auth/),
[yt-dlp](https://github.com/yt-dlp/yt-dlp),
[faster-whisper](https://github.com/SYSTRAN/faster-whisper).
