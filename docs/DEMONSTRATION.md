# Repeatability evidence and technical demonstration

To record your own version, use the [recording directions and screen sequence](TECH_DEMO_RECORDING_GUIDE.md)
and [read-aloud script](TECH_DEMO_SCRIPT.md). The existing AI video stays linked until a replacement is supplied.

Completed AI version: [5:43 technical walkthrough, script, captions, and storyboard](../deliverables/technical-demo/README.md). This shows saved artifacts, not a new live execution. Student review remains pending.

Deadline supplied: Tuesday, October 13, 2026. Live runs must occur during the
assignment week, on two different actual days. Multiple runs on October 10 are
useful recovery evidence but do not meet the different-day requirement.

Suggested demonstration outline (4–6 minutes):

- 0:00–0:45: topic, small-business audience, central question, architecture.
- 0:45–1:30: run `bash run.sh`; show orchestration and independent components.
- 1:30–2:30: trace a published claim through its brief, selection decision, stored
  version, retained quote or transcript segment, and original source URL.
- 2:30–3:30: compare runs on different days: new/changed/unchanged counts, source
  freshness exclusions, and resulting editorial changes or lack of changes.
- 3:30–4:30: demonstrate duplicate handling and an honestly recorded collection
  failure/recovery. Label any intentionally simulated failures.
- 4:30–5:30: explain your review sample, policy revision or correction, and one
  architectural tradeoff. Show the publication links and remaining limitations.

For duplicate replay, run `data/store.sh upsert` again with the same retained
`items.jsonl` and save its output as a separately named replay artifact. The
records should be unchanged and the store should retain the same logical items.
Do not overwrite the original `changes.jsonl`.

If no meaningful new item appears on the second day, report that result. To show
update behavior, use an explicitly labeled replay with a previously withheld,
eligible real item and retain the outputs. Do not fabricate a new development or
backdate a run. The offline tests contain fictional examples and do not substitute
for live research or this demonstration.

Architectural tradeoff to evaluate in your own words: Bash keeps the specified
orchestration boundaries inspectable, while focused Python components handle
JSON, parsing, SQLite, transcription, and model calls. SQLite provides atomic
updates and retained versions, but adds a local index reconstruction step for a
fresh clone. Media caching saves work but needs explicit refresh for silent edits.
