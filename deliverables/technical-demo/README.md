# AI technical demonstration

[Watch/download the MP4](technical-demo.mp4) — **5:43**, approximately 5.3 MB.

Prepared October 16, 2026. This is an AI-written, synthetically narrated walkthrough
of retained repository records, not a recording of a new live pipeline run.
It is separate from the three audience-facing videos. Student review is pending.

- [Narration and timestamps](script.md)
- [Captions](captions.srt) (approximate timing; also embedded in MP4)
- [Storyboard](storyboard.png)
- [Duration, checksum, and scene manifest](manifest.json)
- [Full architecture diagram](../../docs/IMPLEMENTATION.md)
- [Published claim trace](../../docs/CLAIM_TRACE.md)

Validation: all seven scenes visually inspected; full audio/video decode passed.
The MP4 is retained in Git so a fresh public clone includes the demonstration.
GitHub may offer a download rather than inline playback. No external video-platform
upload is claimed.

To reproduce on Windows with Arial fonts, install `requirements-demo.txt` and run
`python publishing/render_technical_demo.py` from the repository root. The script
uses edge-tts with the synthetic en-US-AriaNeural voice, Pillow graphics, and
FFmpeg. Speech synthesis requires internet access. Intermediate media is cached
under `.tools/technical-demo/`; remove the matching cached narration if editing
the script. Caption timing is approximate and should be reviewed during playback.
