# Problem Set 4 Student Submission

**Student:** Student to complete

**GitHub repository:** https://github.com/harrrisw/ps04

**Deadline supplied:** Tuesday, October 13, 2026

**Status:** Pipeline implemented and tested; three October 10 article drafts and matching scripts pass mechanical checks, and the student has uploaded all three videos to YouTube (links below). Student feedback is recorded and implemented in policy version 3. Live collection ran again on October 16. Final source verification, Google Vids/HeyGen production evidence, editorial approval, Substack article publication, and the technical demonstration remain outstanding. October 16 work is after the supplied October 13 deadline.

The original course requirements are retained in [docs/ASSIGNMENT.md](docs/ASSIGNMENT.md),
and the required contracts remain in [ARCHITECTURE.md](ARCHITECTURE.md).

## Topic and Audience

- **Publication name:** The Small Business Research Brief
- **Topic:** AI tools for customer, competitor, and market research on a small-business budget.
- **Audience:** Market researchers, marketing generalists, and small-business owners who understand basic research methods but have limited budget, time, and technical support.
- **Central question:** Where can AI research tools save small businesses time while producing evidence reliable enough to guide decisions?
- **Scope:** Desk research, competitor monitoring, customer-feedback analysis, and interview/survey synthesis. Examine traceability, accuracy, cost, practical effort, and transfer to small-business conditions.
- **Exclusions:** Generic content generation, enterprise-only procurement, unsupported ROI claims, and synthetic respondents presented as observed customers.
- **Voice:** Practical, accessible, and skeptical of unsupported promotional claims.
- **Reason to return:** A recurring evidence check on which capabilities merit a small pilot and which claims still need validation.

## Published Series

The student supplied all three YouTube upload links on October 16, 2026. YouTube's
oEmbed endpoint returned the matching titles and channel **Harris Wang** without
authentication for all three. Unlisted YouTube videos are acceptable; public
listing is not required. Full playback has not been independently checked.
Substack article links remain pending.

[Three narrated MP4 review copies and matching articles](docs/VIDEO_REVIEW.md) are available locally. The videos
run 4:43, 4:12, and 4:31 and passed full audio/video decoding. They were rendered
locally with synthetic narration; Google Vids/HeyGen production is still pending.
The student subsequently requested local delivery. The six files, captions, source
descriptions, and checksums are saved in [the local delivery folder](deliverables/20261010T052912Z-1d2e8a/)
and [ZIP archive](deliverables/20261010T052912Z-1d2e8a.zip). Local delivery does not
satisfy the assignment's separate external publication requirement.

The [current review packet](runs/20261010T052912Z-1d2e8a/REVIEW.md) links all six
drafts and their supporting passages. [Assistant copy edits](runs/20261010T052912Z-1d2e8a/assistant_edits/20261010-copy-edit/README.md)
preserve original outputs and diffs; they are not student corrections or approval.

| Piece | Purpose | Substack article | YouTube video |
| --- | --- | --- | --- |
| 01 | What changed and why it matters | Pending publication | [AI for Competitor Research: Check the Evidence Before You Automate](https://youtu.be/qWxMqmFNnIw) |
| 02 | Which claims withstand scrutiny | Pending publication | [Can You Trust AI Research? How to Check Its Claims](https://youtu.be/Ej1c8o_LTf8) |
| 03 | Implications and what to watch | Pending publication | [Is AI Research Worth the Effort? Run a Small-Business Pilot](https://youtu.be/oUOU5CditYM) |

The upload mapping and verification scope are retained in
[publication_links.json](runs/20261010T052912Z-1d2e8a/publication_links.json).
Uploading the local renders does not by itself document Google Vids/HeyGen production.

**Separate 4–6 minute technical demonstration:** Not yet recorded.

## Setup and Execution

See [docs/SETUP.md](docs/SETUP.md) for dependencies, platform details, configuration,
independent stage commands, caching behavior, and evidence restoration. Tested
package versions are recorded in [requirements-lock.txt](requirements-lock.txt).

```bash
bash run.sh
bash run.sh --package runs/RUN_ID
```

On this Windows machine, invoke Git Bash from PowerShell:

```powershell
& 'C:/Program Files/Git/bin/bash.exe' run.sh
& .tools/python/python.exe tests/test_pipeline.py
```

The project uses Bash orchestration and focused Python components. Current AI
transport for the retained October 10 drafts was Codex with the existing ChatGPT login.
The root configuration now selects MIT Parley (`gpt-5.4-mini`). Authenticated model
discovery succeeded; the supplied `openai` alias was rejected as unsupported and
replaced with a model ID returned by MIT's API. Live generation records are in
the October 16 run artifacts. See [Parley setup](docs/PARLEY.md). The configured model is
resolved and recorded when available; older attempts explicitly report an
unreported default. Direct commercial API providers are not configured. Local Ollama is an
optional alternative. Audio without timed captions uses faster-whisper base.en
on CPU. Parley reads `PARLEY_API_KEY` or the explicitly shared Git-ignored local key; secrets
are not stored in configuration or logs. `CODEX_BIN` and `PIPELINE_PYTHON` optionally
select executable paths. Actual AI dollar cost is unknown; local software costs
exclude hardware, electricity, and any existing account subscription.

## Architecture and Manual Handoffs

The component contracts are in [ARCHITECTURE.md](ARCHITECTURE.md). All 16 required
Bash entry points are implemented. The two workflows only coordinate their stages.
Each substantive component has its own focused Python implementation. Only
`data/store.sh` and its owning implementation read/write the persistent index.
JSON Lines connect stages, including a real pipe from candidates to extraction.

AI is called during selection, briefing, article drafting, and script drafting.
Exact requests, responses, JSON schemas, and usage events live in each run's
`ai_calls/` directory. There is no simulated model fallback in live mode.

The pipeline stops for human review. Matching approval is required before packaging,
and content changes invalidate that approval. Google Vids production, Substack and
YouTube publishing, link verification, and the technical demonstration remain
manual handoffs. See [docs/HUMAN_REVIEW.md](docs/HUMAN_REVIEW.md) and
[docs/PRODUCTION.md](docs/PRODUCTION.md).

## Evidence and Runs

The local index is `data/evidence/index.sqlite3` (ignored by Git). Retained evidence
is in [data/assets](data/assets/), with immutable text/transcript versions and
provenance. Run artifacts preserve ingestion records and can reconstruct the index
through `bash scripts/restore_evidence.sh`. Large downloads in `data/media/` are
ignored; retrieve written pages and YouTube media from each record's `url`, and
podcast audio from `media_url`.

| Attempt | Actual UTC date | Artifacts | Result |
| --- | --- | --- | --- |
| Initial live attempt | 2026-10-10 | [Run 21091d](runs/20261010T051736Z-21091d/) | 25 extracted items; channel, transcription-library, and sandbox-login failures preserved. |
| First completed editorial selection | 2026-10-10 | [Run 15fd8c](runs/20261010T052041Z-15fd8c/) | 28 distinct items, seven producers, two videos and two podcasts. Three accepted, 21 rejected, four deferred. Insufficient accepted media blocked briefs. |
| Revised sources and proposed policy | 2026-10-10 | [Run 1d2e8a](runs/20261010T052912Z-1d2e8a/) | 39 eligible items, nine publishers; 35 written, two videos, two podcasts. 13 accepted, 23 rejected, three deferred. Three article/script pairs pass mechanical checks; student review pending. |
| October 16 Parley attempt | 2026-10-16 | [Run b61328](runs/20261016T043111Z-b61328/) | Collection completed: 55 eligible items, eight publishers, two videos and two podcasts. Initially lacked the key; a later retry reached MIT but rejected the unsupported `openai` alias. |
| October 16 Codex fallback | 2026-10-16 | [Run bdfa88](runs/20261016T043723Z-bdfa88/) | Collection completed; editorial selection stopped at the account usage limit. This is a failed attempt, not a completed series. |
| Parley selection with supported model | 2026-10-16 | [Run 4d1cfc](runs/20261016T153150Z-4d1cfc/) | 58 eligible items; 13 accepted, 30 rejected, 15 deferred. No accepted YouTube item, so briefing was correctly blocked. |
| Parley series with relevant webinar | 2026-10-16 | [Run 231399](runs/20261016T153525Z-231399/REVIEW.md) | 60 eligible items, nine publishers; 15 accepted, 30 rejected, 15 deferred. Three articles and scripts pass checks after documented assistant citation and copy edits. Nine items from six publishers contribute, including all three input kinds. |

These are genuinely different-day live collections from the October 10 runs.
They occurred after the supplied deadline and do not establish completion within
the original assignment week. The final Parley series required assisted recovery;
[brief corrections](runs/20261016T153525Z-231399/assistant_edits/brief_repair/README.md)
and [content edits](runs/20261016T153525Z-231399/assistant_edits/content_copy_edit/README.md)
preserve the original outputs and the reasons for changes. Its new scripts have
not been rendered; the local delivery bundle retains the October 10 matching pairs.

[The October 10-to-16 comparison](runs/20261016T153525Z-231399/feedback_comparison.md)
records changed eligible evidence, decisions, policy, and arguments. Source coverage,
model provider, date window, and policy all changed; the comparison cannot isolate
the policy's causal effect.

The first two attempts took approximately 47 seconds and 433 seconds respectively;
see their summaries and per-stage receipts for details. Paid API spending was not
enabled. The revised run used approximately 672 seconds of active stage time,
including retries; its longer wall span includes a pause between work sessions.
Unreported account usage costs are marked unknown, not zero.

[The unchanged replay](runs/20261010T052041Z-15fd8c/replays/store-e46554b8/replay.json)
re-ingested all 28 retained items: every result was unchanged, the store retained
28 logical items, and latest versions were identical. This is labeled replay, not
a second live run. Each run retains mechanical date exclusions. Actual collection
failures and recovery are recorded in receipts. The tests use clearly fictional
data in disposable isolated copies and do not count as live evidence.

**Published claim trace:** Pending final reviewed/published content. The inspectable
chain is article/script claim marker → brief claim → decision → item/version → exact
text quote or transcript segment → source URL and timestamp. Do not describe an
unpublished draft as a published claim.

## Editorial Review

- Current policy: [config/editorial_policy.md](config/editorial_policy.md).
- Exact historical policy and prompts: each run's `config/` and `prompts/` snapshots.
- Student feedback: [six-item review record](runs/20261010T052912Z-1d2e8a/human_review_sample.md), covering the expanded October 10 collection.
- Implemented revisions: [policy change rationale](docs/POLICY_CHANGE_PROPOSAL.md).
- Source independence and missing perspectives: [docs/SOURCES.md](docs/SOURCES.md).

The following judgments were supplied by the student on October 16, 2026 and
expanded into prose with AI assistance. They agree with the six corresponding
decisions in the expanded October 10 run. The linked review record preserves the
student's original comments and the exact item/version identifiers. Source and
audio verification have not been reported; these comments do not constitute final
approval of the article/video series.

### Three sources I accept

**1. Nielsen Norman Group — [Empathy Mapping: The First Step in Design Thinking](https://www.nngroup.com/articles/empathy-mapping/)**

I accept this source because it helps translate research theory into an actual
pipeline. Its requirement to connect findings to research material gives me a
concrete way to assess AI-assisted synthesis: retain the original interviews or
survey responses, link each proposed finding to supporting evidence, and flag
unsupported statements as assumptions. This makes the method useful for a small
team that needs an understandable review process. I would use it to justify how
the pipeline checks findings, while keeping claims about time savings or improved
accuracy separate until those outcomes are measured.

**2. Crayon — [Insights API](https://www.crayon.co/blog/insights-api)**

I accept this source because it directly addresses the competitive landscape and
provides a concrete capability to examine. Access to the underlying text and
source links offers a specific connection between a competitor update and the
evidence behind it. That is the useful certainty here: the vendor describes a
feature that a pilot can check. It does not establish that every resulting
summary is correct or that the product is affordable for a small business. I
would use the announcement to motivate a competitor-monitoring pilot, then assess
accuracy, access costs, and implementation effort before recommending adoption.

**3. Marketing AI Institute — [How to Use AI Agents to Fact-Check and Copy Edit Your Content](https://www.marketingaiinstitute.com/blog/ai-agents-as-fact-checkers)**

I accept this source because its use of multiple agents to check information is
an intriguing workflow. Dividing a research memo into topics, checking claims
against the supplied sources, and having another agent examine proposed
corrections makes the review process concrete enough to explore. I am especially
interested in whether this could help a small team identify claims needing human
attention. Agreement between agents would still need to be checked against the
original evidence. I would treat the workflow as a useful pilot idea, with its
accuracy and time-saving benefits left to evaluation.

### Three sources I defer

**1. Crayon — [7 Ways Competitive Enablement Boosts Intel Adoption](https://www.crayon.co/blog/7-ways-competitive-enablement-boosts-intel-adoption)**

I defer this source because the framework needs stronger supporting evidence
before I would rely on its outcome claims. Delivering competitor information
within existing workflows is relevant, but the reported association between
AI-agent use and revenue impact does not establish that the agents caused the
improvement. I would want to inspect the survey methods, sample composition,
definitions of revenue impact, and representation of small businesses. That
would help me judge whether the framework is supported well enough to guide
decisions for this audience. Until then, I would retain it as a research lead.

**2. Christopher Penn — [Supercharge AI Agents with Lexical-Semantic Fusion to Cut Costs and Boost Accuracy](https://www.christopherspenn.com/2026/10/supercharge-ai-agents-with-lexical-semantic-fusion-to-cut-costs-and-boost-accuracy)**

I defer this source because I want a worked comparison or measured baseline for
its claims about speed and cost savings. A useful comparison would run the same
research questions over the same document collection using the current search
workflow and the proposed combined lexical-semantic approach. It should record
setup effort, processing time, human checking and correction time, and actual
API or computing costs, while assessing the relevance and completeness of the
results. Faster retrieval alone would not establish a saving if preparation or
review took longer. These are the measurements I would request before accepting
the claimed benefits; I have not conducted that comparison.

**3. The Artificial Intelligence Show — [Episode 245](https://www.youtube.com/watch?v=X-JA9VVnUBs)**

I defer this source because the discussion centers on announcements and
hypothetical applications rather than a tested research workflow. It may help
identify developments to investigate, but it does not yet show how a small
business would complete a market-research task and check the result. I would
want a concrete example with identifiable inputs, steps, outputs, verification,
and costs, supported by primary documentation for the announced capabilities.
That would make it possible to assess practical value instead of relying on
what the tools might eventually do.

### Policy revision and remaining review

The assistant proposed policy version 2 before these student comments, after
version 1 rejected or deferred all media. It distinguishes evidence for an
attributed experience from evidence for measured effectiveness. The six comments
above emphasize practical, inspectable workflows and stronger evidence for
performance claims. Policy version 3 implements these comments, and October 16
runs snapshot that revision. This implementation is AI-assisted and does not
claim additional student source verification. Source/audio verification, any
factual corrections, and final series approval remain pending. The earlier
October 10 comparison is preserved as prior work, not a rerun caused by this
October 16 feedback.

## Reflection — student to complete

- **One insight the system produced:** Explain a supported synthesis after reviewing the actual briefs and sources.
- **One editorial failure or limitation:** Consider the initial mismatch between the evidence standard and attributed interview claims, the commercially weighted sources, or a limitation you identify yourself.
- **Next improvement:** Explain which change would most improve the system and why.
- **Architectural tradeoff:** Explain why separate Bash interfaces plus focused Python components and a versioned SQLite store suit this project, including the cost of rebuilding the local index and verifying media-cache freshness.

See [docs/DEMONSTRATION.md](docs/DEMONSTRATION.md) for a technical demonstration outline
and the remaining repeatability requirements.
