# Implementation validation

## October 16 live checks

- [Run 231399](../runs/20261016T153525Z-231399/summary.json) completed collection,
  Parley selection, article generation, script generation, and final checks with
  **documented assistant editorial repair**. It retained 60 eligible items from
  nine publishers; 15 were accepted, 30 rejected, and 15 deferred. Three articles
  and three scripts pass mechanical checks, using nine items from six publishers
  across all three input kinds. This is not an unattended success: initial briefs
  and the model's correction contained invalid quotations. The assistant corrected
  citations and narrowed claims in [the retained edit record](../runs/20261016T153525Z-231399/assistant_edits/brief_repair/README.md),
  then repaired draft citation formatting and length. Student source/audio review
  remains outstanding. These fresh scripts have not been rendered into videos.

- The authenticated MIT Parley model endpoint accepted the student's key. The
  example `openai` alias returned HTTP 400; `gpt-5.4-mini` is listed by the API and
  successfully completed all 15 selection batches in
  [run 4d1cfc](../runs/20261016T153150Z-4d1cfc/summary.json).
- That run collected 58 eligible items from eight publishers and recorded 13
  accepts, 30 rejects, and 15 deferrals. Neither YouTube episode was accepted, so
  the evidence-coverage guard correctly blocked briefing. It is a verified live
  API/selection run, not a successful complete generation run.
- The earlier [run b61328](../runs/20261016T043111Z-b61328/summary.json) completed
  collection with local YouTube and podcast transcription, Deno, curl-cffi, and
  FFmpeg. Its generation failures (missing key, then unsupported model alias)
  remain in receipts. The Codex fallback stopped at an account usage limit.
- Three October 10 articles contain approximately 730, 758, and 758 words. Their
  matching locally rendered videos run 4:43, 4:12, and 4:31. Full FFmpeg audio/video
  decoding passed, and the exported ZIP passed its integrity check. See
  [local files](VIDEO_REVIEW.md). No Google Vids/HeyGen production or publication
  is claimed.

## Automated checks

The offline suite passed **27 tests** on October 16, 2026 using Python 3.12.10 and
Git Bash 5.2.37 on Windows. These are isolated fictional fixtures, not research
evidence or simulated student approval for a live run.

Coverage includes:

- Starter-provided version history and ordered duplicate replay expectations.
- Interleaved duplicates, rollback on version collisions, and malformed JSON.
- Inclusive 30-day boundaries, unknown/future/invalid dates, and original page dates.
- Partial collection failure with usable records and honest receipts.
- Full entry-point failure with saved snapshots and a final summary.
- A workflow returns nonzero when completed content checks find blocking errors;
  completing the assessment does not itself count as a passing series.
- Exact quote, timestamp, publisher-count, and cross-source synthesis checks.
- One bounded brief-correction request after citation failure, including the
  specific invalid references; unsupported corrections still fail validation.
- Packaging without approval, stale approval after edits, and evidence tampering.
- Audience-facing source links survive removal of internal claim markers; missing
  source links are derived from the brief's evidence records.
- Preservation of entered publication links and removal of internal claim markers.
- JSON3/VTT timestamps and rejection of transcripts without timed segments.
- Exact model-response reuse without inference and invalidation when input changes.
- MIT Parley request construction, usage accounting, missing credentials, redacted
  HTTP errors, blocked redirects, invalid/truncated answers, schema rejection, and
  absence of keys from saved artifacts, and the explicit Git-ignored key handoff.
  These transport tests use mocked responses. The PowerShell key helper also passed syntax parsing.
- Actual yt-dlp recognition of the installed Deno runtime when runtime discovery
  through PATH is unavailable.
- Local YouTube transcription bypasses both subtitle download options and supplies
  the detected FFmpeg location to yt-dlp.

A separate live metadata-only check of the configured YouTube video
`Z4Coq_GIcpo` recognized Deno 2.9.7 and returned 25 formats, including three with
audio, with no warnings. It used yt-dlp 2026.8.19 and yt-dlp-ejs 0.8.0, downloaded
no media, and made no LLM API calls. This confirms runtime discovery and format
extraction for that video; it is not a full pipeline run or a guarantee against
future YouTube rate limits.

Commands:

```powershell
& .tools/python/python.exe tests/test_pipeline.py
```

The 16 required Bash files also passed Bash syntax validation, and the Python
components compiled successfully. Real runs separately demonstrated RSS discovery,
substantive extraction, YouTube audio/captions, local podcast transcription,
existing-account model inference, source selection, and persisted failure/recovery.
The [current content review](../runs/20261010T052912Z-1d2e8a/review.json) passes:
39 eligible items from nine publishers, with eight items from seven publishers
used across the three article/script pairs. All three input kinds contribute to
the series. The remaining warning requires human judgment on meaning, credibility,
media quotations, and article/script consistency. Passing tests does not establish
the credibility of a claim or replace the student's judgment.
