# Technical demonstration narration

AI-written and synthetically narrated. Saved-artifact walkthrough, not a live run. Student review pending.

## 00:00:00 — A research pipeline you can inspect

This is an AI-narrated technical walkthrough of the Small Business Research Brief. The audience is small-business market researchers who need useful evidence without a large research budget. The project asks where AI tools deserve a practical pilot, and where their claims still need testing. Three articles and their matching videos have been published. This demonstration walks through real saved files and records. It does not show a new live execution, and it does not substitute for the student reviewing the work or explaining the architecture.

Record: `SUBMISSION.md`

## 00:00:36 — Separate stages, one evidence trail

The entry point is bash run dot sh. Sixteen Bash interfaces divide orchestration, collection, storage, editorial work, checking, and packaging. The collectors discover feeds, YouTube videos, and podcasts. Extraction produces substantive text or timed transcripts. JSON Lines carry records between stages. Only the store component accesses the SQLite evidence index. Filtering applies the thirty-day window. AI then selects sources, develops briefs, and drafts articles and video scripts. Checks precede human review. Packaging requires an approval fingerprint that matches the reviewed content. The architecture diagram and component contracts are preserved in the repository.

Record: `run.sh  |  docs/IMPLEMENTATION.md  |  data/store.sh`

## 00:01:31 — Trace a published claim to its source

Here is one published claim. Article one says Crayon describes access to underlying text and source links. The saved source passage says, Ask for more and you get the full text and source link. The evidence record has a stable item identifier and an immutable version identifier. Its editorial decision is accept, and brief claim zero one C zero one carries the supporting citation. The published article attributes this capability to the vendor. It does not turn the announcement into independent proof of accuracy, affordability, or business effectiveness. The claim-trace document links the exact retained files.

Record: `runs/20261010T052912Z-1d2e8a/briefs.jsonl`

## 00:02:16 — Two actual collection dates

The published October tenth series used thirty-nine eligible items from nine publishers. The final October sixteenth run used sixty eligible items, also from nine publishers, and produced another three articles and scripts. Those later drafts are retained separately from the published series. Its immediate collection batch recorded two new and thirty-eight unchanged records; those counts are not the comparison against October tenth. The saved comparison documents changes in evidence and editorial decisions. Because the date window, sources, model provider, and policy changed together, the comparison cannot isolate a policy effect. October sixteenth was after the supplied deadline.

Record: `runs/20261016T153525Z-231399/feedback_comparison.md`

## 00:03:04 — Replay and recovery remain visible

The duplicate demonstration re-ingested exactly twenty-eight saved items. Every record was unchanged, the store still held twenty-eight logical items, and the latest versions stayed identical. This is explicitly labeled a replay, not another live collection day. Failure records are preserved too. YouTube subtitle throttling motivated local audio transcription, with Deno and FFmpeg supporting media extraction. An unsupported Parley model alias failed before a supported model identifier was configured. A later run also stopped briefing because no YouTube source had been accepted. Adding a relevant webinar enabled the next attempt without weakening that coverage check.

Record: `runs/20261010T052041Z-15fd8c/replays/store-e46554b8/replay.json`

## 00:03:53 — Human feedback changes the policy

The student supplied three accept judgments and three defer judgments. They favored practical workflows, inspectable competitor evidence, and a concrete multi-agent checking process. They requested stronger evidence for frameworks, measured baselines for speed and cost claims, and tested workflows behind announcements. Policy version three records that revision. The October sixteenth generation still needed assistance: invalid quotations remained after an automated repair, and documented assistant edits corrected their source attribution. Original and corrected outputs are retained. These assistant corrections are not presented as student corrections or final approval. Mechanical checks passing still leaves source interpretation for human review.

Record: `config/editorial_policy.md  |  docs/POLICY_CHANGE_PROPOSAL.md`

## 00:04:46 — Tradeoffs and the submission boundary

The main architectural tradeoff is inspectability versus operational complexity. Separate Bash interfaces make each stage easy to inspect and replay; Python handles parsing, model calls, and storage. Immutable evidence preserves provenance, but a fresh clone must reconstruct the ignored SQLite index. Media caching reduces repeated downloads and transcription, while silent source edits may require an explicit refresh. Actual model dollar cost remains unknown where the provider did not report it. The submission links the six publications, all retained attempts, and this demonstration. Remaining requirements include Google Vids or HeyGen production evidence, final human verification, and the student reflection. This AI-generated walkthrough is ready for the student to review.

Record: `docs/EVALUATION.md  |  docs/RUNS.md  |  SUBMISSION.md`
