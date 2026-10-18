# Voice-cloned video production

The student requested three revised audience videos and a fourth architecture
walkthrough using their own voice likeness, and supplied a reference recording.
The recording is kept locally in ignored `.tools/voice-reference/`. It is not
included in the public repository or sent to a hosted speech-generation service.

The local production entry point is `publishing/chatterbox_videos.py`. It preserves
the original October 10 scripts and visuals for pieces 01–03, adds a visible voice
disclosure, and retimes scenes and captions to the generated speech. Piece 04
uses the technical walkthrough with an updated diagram and reflection status.
It describes retained runs rather than showing a new pipeline execution.

## Model and environment

This workstation uses CPU inference with **ResembleAI/chatterbox-nano**, accessed
through the official `ChatterboxTurboTTS` class with `nano=True`. The model and
source revisions observed during setup, along with checkpoint hashes, are saved
in the delivery folder's `production_sources.json`. Chatterbox's Perth watermark
is retained. On-screen and accompanying text identify the voice as AI-generated.

Dependencies live in `.tools/chatterbox-env/`, separate from the research pipeline.
The setup uses CPU PyTorch and torchaudio 2.6.0, the official Chatterbox source,
and the official Perth source. It omits the unused Gradio user interface. The
environment's package list is saved with the final deliverables for reproduction.

Official references: [Chatterbox source and usage](https://github.com/resemble-ai/chatterbox),
[Nano model](https://huggingface.co/ResembleAI/chatterbox-nano),
and [Perth watermarking](https://github.com/resemble-ai/Perth).

## Commands in this workspace

Run from the repository root in PowerShell:

```powershell
# Create the narration jobs and new frames without modifying historical runs.
& .tools/python/python.exe -X utf8 publishing/chatterbox_videos.py prepare

# Generate speech locally in the isolated environment.
& .tools/chatterbox-env/Scripts/python.exe -X utf8 publishing/chatterbox_videos.py synthesize

# Screen speech for omissions/repetitions with local Whisper transcription.
& .tools/python/python.exe -X utf8 publishing/check_chatterbox_audio.py

# Render four MP4s, captions, storyboards, and a checksum/duration manifest.
& .tools/python/python.exe -X utf8 publishing/chatterbox_videos.py render
```

Generation reuses existing audio chunks. If editing narration, move the affected
chunk files out of `.tools/chatterbox-production/audio/` before regenerating; do
not reuse cached speech against a changed script. Review any flagged transcription
differences in `audio_checks.json`: automated transcription is imperfect and does
not judge speaker similarity or replace listening.

Output goes to `deliverables/20261017-chatterbox/`. Large MP4s remain local under
the existing Git ignore rules. The historical videos and public links remain
unchanged until replacement uploads are supplied. These local renders do not
establish Google Vids/HeyGen production or final editorial approval.
