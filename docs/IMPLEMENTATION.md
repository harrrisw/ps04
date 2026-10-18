# Implemented pipeline architecture

Run `bash run.sh` from the repository root. The course contracts remain unchanged
in [ARCHITECTURE.md](../ARCHITECTURE.md) and [README.md](../README.md).

```mermaid
flowchart TD
    R[run.sh: date and snapshot] --> C[workflows/collect_sources.sh]
    C --> F[collectors/fetch_feeds.sh]
    C --> Y[collectors/fetch_youtube.sh]
    C --> P[collectors/fetch_podcasts.sh]
    F --> E[processing/extract_content.sh]
    Y --> E
    P --> E
    E --> D[data/store.sh: immutable evidence versions]
    D --> W[processing/filter_items.sh: 30-day window]
    W --> S[workflows/create_series.sh]
    R --> S
    S --> A[editorial/select_items.sh]
    A --> B[editorial/create_briefs.sh]
    B --> N[content/write_articles.sh]
    B --> V[content/write_video_scripts.sh]
    N --> K[review/check_content.sh]
    V --> K
    K --> H[Student editorial review and approval]
    H --> X[publishing/prepare_package.sh]
    X --> M[Google Vids or HeyGen and platform publication]
    R --> T[reporting/summarize_run.sh]
```

The diagram is Mermaid source retained in Git and rendered by GitHub. All sixteen
required Bash files have their original responsibilities. Each substantive stage
calls its own Python implementation; `lib/` contains runtime, record, and model
transport helpers rather than a hidden whole-pipeline implementation.

The collectors emit JSON Lines. Extraction retrieves full written text or
timestamped media transcripts; local Whisper avoids YouTube's rate-limited subtitle
endpoint. Only `data/store.sh` and `data/store.py` access the SQLite index. Other
components use the store's commands. Source files and immutable transcripts are
retained in `data/assets/`; the ignored index can be reconstructed using
`bash scripts/restore_evidence.sh`.

Selection, briefing, article generation, and script generation call the configured
LLM. The October 10 series used Codex; the completed October 16 series used MIT
Parley with `gpt-5.4-mini` and documented assistant corrections. Exact requests,
responses, schemas, and usage are retained under each run's `ai_calls/` directory.
Failed attempts remain recorded. Dollar cost stays unknown when the provider does
not report it; account credits are not assumed free.

Checks validate source eligibility, exact quotations, transcript segments,
independent-publisher coverage, and claim markers. They do not prove semantic
correctness. Packaging requires a matching human approval fingerprint. Publishing
outside the package flow is recorded as an external student action and does not
create or backdate approval.

See [all retained runs](RUNS.md), [published claim traces](CLAIM_TRACE.md),
[setup](SETUP.md), and [evaluation audit](EVALUATION.md).

## Local voice-cloned video revision — October 17

The [Chatterbox production workflow](CHATTERBOX_PRODUCTION.md) adds a local media
revision path after the saved scripts. It does not change the sixteen research
components, modify the historical evidence, or create editorial approval.

```mermaid
flowchart LR
    S[Saved scripts and visual scenes] --> C[Chatterbox Nano on CPU]
    V[Private student voice recording] --> C
    C --> A[Generated speech chunks with Perth watermark]
    A --> Q[Whisper back-transcription screening]
    A --> F[FFmpeg scenes and captions]
    S --> F
    Q --> H[Playback and human review]
    F --> H
    H --> L[Four local revised MP4s]
    L --> P[Google Vids or HeyGen handoff and manual upload]
```

The reference recording and model files remain in ignored `.tools/`; large video
revisions remain local. Synthetic voice narration is disclosed. Original public
uploads retain their existing links until replacement uploads are provided.
