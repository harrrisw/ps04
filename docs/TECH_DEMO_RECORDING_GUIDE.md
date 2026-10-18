# Record your technical demonstration

Target **5:20–5:50**; the assignment allows **4–6 minutes**. Record your screen
and your voice. A face camera is optional. Use the
[read-aloud script](TECH_DEMO_SCRIPT.md), adapting it to wording you can explain.
The script was prepared with AI assistance from the repository's actual records.

## Before recording

1. Use your screen recorder with microphone audio enabled. Choose a 1080p screen
   recording if available. Record a ten-second sample and check sound and text.
2. Increase the editor/browser text size until individual records are readable.
   Enable word wrap for JSON Lines files. Close unrelated tabs and notifications.
   Keep `.secrets/`, API keys, account settings, and terminal history off screen.
3. Keep the script on another screen or device. Record only the demonstration
   window if your recorder supports it.
4. Open the files below beforehand. In VS Code, Ctrl+P opens a file by path;
   Ctrl+F finds an identifier. Use GitHub's rendered page for the Mermaid diagram.
5. Rehearse once with a timer. Pause recording during long file navigation if
   needed. Keep the result under six minutes without speeding up your speech.

## Screen sequence

The times are pacing targets, not measured narration durations.

| Time | Show | Action |
| --- | --- | --- |
| 0:00–0:30 | [SUBMISSION.md](../SUBMISSION.md) | Show topic/audience, then the three article/video pairs. |
| 0:30–1:15 | [Rendered architecture](https://github.com/harrrisw/ps04/blob/main/docs/IMPLEMENTATION.md), then [run.sh](../run.sh) | Show the diagram, then point to collection, series creation, and reporting calls. Explain `bash run.sh`. |
| 1:15–2:15 | [Claim trace](CLAIM_TRACE.md), [source text](../data/assets/c3df7e6b65257849c66ba049/b192c0ca1da12bd242489506681f276f83473000ed4152d9795eac13ccc33ed1/text.txt), [decisions](../runs/20261010T052912Z-1d2e8a/decisions.jsonl), [briefs](../runs/20261010T052912Z-1d2e8a/briefs.jsonl), [published article](https://mingxiwang.substack.com/p/pilot-the-evidence-trail-before-automating) | Locate the quote, the acceptance, claim `01-C01`, and the article's “What source access changes” section. |
| 2:15–3:00 | [Run inventory](RUNS.md), [October 10 summary](../runs/20261010T052912Z-1d2e8a/summary.json), [October 16 summary](../runs/20261016T153525Z-231399/summary.json), [comparison](../runs/20261016T153525Z-231399/feedback_comparison.md) | Show eligible counts and actual dates. Briefly show how the saved comparison records editorial changes. |
| 3:00–3:40 | [Duplicate replay](../runs/20261010T052041Z-15fd8c/replays/store-e46554b8/replay.json), [repair record](../runs/20261016T153525Z-231399/assistant_edits/brief_repair/README.md) | Highlight `all_unchanged`, `same_latest_versions`, and the documented invalid-quotation recovery. |
| 3:40–4:30 | [Your feedback](../runs/20261010T052912Z-1d2e8a/human_review_sample.md), [policy v3](../config/editorial_policy.md) | Show an accept and a defer judgment; highlight the rule requiring a measured baseline for speed/cost claims. |
| 4:30–5:30 | [Architecture](IMPLEMENTATION.md), then [evaluation checklist](EVALUATION.md) | Explain the tradeoff, published outputs, and remaining limits. |

### Search strings for the claim trace

Copy these into Ctrl+F ahead of time:

- Source text: `Ask for more and you get the full text and source link`
- Decisions: `feed:32944883b9dff85a7148008d`
- Briefs: `01-C01`
- Published article: `What source access changes`

The claim-trace document contains the full immutable version identifier. Show it
on screen; you do not need to read that long identifier aloud.

## What to run

You can present the completed second run using its retained records. Say clearly
that you are showing saved runs. A new full collection is unnecessary for this
recording and would use the current date, network access, and model credits.

Show this entry-point command in Git Bash, or point to it in the documentation:

```bash
bash run.sh
```

You do not have to press Enter during the five-minute recording. Do not imply you
executed it if you only displayed it. If you choose to record a new run, allow it
to finish beforehand, preserve its new run folder, and identify its real date.
Do not substitute that run's counts into the script without checking them.

Optional local verification before recording, from PowerShell in the repo root:

```powershell
& .tools/python/python.exe -X utf8 tests/test_pipeline.py
```

This uses fictional test fixtures and does not constitute a live research run.
Showing the test result is optional; prioritize the actual evidence trace.

## After recording

- Play back the file: check audio, readable records, and a duration of 4–6 minutes.
- Confirm the evidence trace, second run, duplicate/recovery record, feedback,
  policy revision, and architectural tradeoff are visible.
- Keep disclosures accurate. Assistant citation repairs are separate from your
  six source judgments. Do not say source/audio verification or Google Vids
  production is complete unless you have actually completed it.
- Upload the technical demonstration to YouTube as **unlisted** or public. This
  is a fourth, separate video, not a replacement for the three audience videos.
- Suggested title: **Small Business Research Brief — Pipeline Technical Demo**.
- Include the repository link in its description:
  `https://github.com/harrrisw/ps04`.
- Open the uploaded link while signed out, then supply that link so the submission
  can point to your recording. Until then, the existing AI-demo link remains valid.
