# All retained run attempts

Dates are actual UTC execution dates. October 16 is after the supplied October 13 deadline. Partial and failed attempts remain inspectable; none are relabeled as completed series.

| Run | Eligible | Accept / reject / defer | New / changed / unchanged | Outcome |
| --- | --- | --- | --- | --- |
| [20261010T051736Z-21091d](../runs/20261010T051736Z-21091d/) | 25 | — / — / — | 25 / 0 / 0 | Initial collection: channel, transcription-library, and login failures retained. |
| [20261010T052041Z-15fd8c](../runs/20261010T052041Z-15fd8c/) | 28 | 3 / 21 / 4 | 3 / 0 / 25 | Selection completed; no acceptable media coverage for briefs. Separate duplicate replay retained. |
| [20261010T052912Z-1d2e8a](../runs/20261010T052912Z-1d2e8a/) | 39 | 13 / 23 / 3 | 11 / 0 / 28 | Published October 10 series. Mechanical checks passed after documented assistant copy edits; final approval unrecorded. |
| [20261016T042059Z-e61565](../runs/20261016T042059Z-e61565/) | — | — / — / — | — / — / — | Partial attempt: no summary or completed series retained. Do not infer a completed run or an undocumented cause. |
| [20261016T042501Z-a1f14a](../runs/20261016T042501Z-a1f14a/) | — | — / — / — | — / — / — | Partial attempt: no summary or completed series retained. Preserve available discovery/extraction records. |
| [20261016T043111Z-b61328](../runs/20261016T043111Z-b61328/) | 55 | — / — / — | 21 / 0 / 18 | Collection completed; missing-key attempt followed by unsupported Parley model alias failure. |
| [20261016T043723Z-bdfa88](../runs/20261016T043723Z-bdfa88/) | 55 | — / — / — | 0 / 0 / 39 | Collection completed; Codex fallback stopped at account usage limit. |
| [20261016T153150Z-4d1cfc](../runs/20261016T153150Z-4d1cfc/) | 58 | 13 / 30 / 15 | 3 / 0 / 36 | Supported Parley model selected sources; no accepted YouTube item blocked briefing. |
| [20261016T153525Z-231399](../runs/20261016T153525Z-231399/) | 60 | 15 / 30 / 15 | 2 / 0 / 38 | Parley series passed checks after retained assistant citation and copy edits. Later drafts are not the published series. |

New/changed/unchanged counts describe that attempt’s ingestion against the then-current index; they are not automatically a comparison against October 10. See the [explicit October 10–16 comparison](../runs/20261016T153525Z-231399/feedback_comparison.md). It preserves the changed evidence, decisions, and policy without claiming an isolated policy effect.

The [duplicate replay](../runs/20261010T052041Z-15fd8c/replays/store-e46554b8/replay.json) re-ingested 28 saved items: all unchanged, 28 logical items retained, latest versions identical. This is a replay, not a second day.

Within each completed run inspect `run.json`, `config/`, `prompts/`, `items.jsonl`, `changes.jsonl`, `eligible.jsonl`, `exclusions.jsonl`, `decisions.jsonl`, `briefs.jsonl`, `ai_calls/`, `logs/`, `usage.jsonl`, `review.json`, and `summary.json` where present. Missing downstream files in failed attempts indicate the point reached, not successful completion. `stage_history/` and `assistant_edits/` preserve superseded outputs and repairs.

Evidence versions and transcripts live in [data/assets](../data/assets/); [setup](SETUP.md) documents rebuilding the local index. [Artifact hashes](audit/artifact_inventory.json) preserve a checkable inventory. Historical summaries retain the status at generation; current publication status is in [SUBMISSION](../SUBMISSION.md).
