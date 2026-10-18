# Technical demonstration — read-aloud script

Approximately five to six minutes with brief navigation pauses. Read only the
quoted narration; the screen cues are directions. Replace `[your name]` and
rephrase anything you would not naturally say. This is an AI-assisted script
based on the saved records, not a statement that you personally performed every
implementation or verification step.

## 1. Project and audience — 0:00

**Screen:** SUBMISSION: topic and publication links.

> Hi, I'm [your name]. This project is the Small Business Research Brief, a
> research pipeline for market researchers working with small-business budgets.
> The question is where AI tools offer useful research capabilities, and what
> evidence we need before trusting their results. The output is three connected
> Substack articles with matching YouTube videos. I'll demonstrate the architecture
> and evidence trail using the saved October tenth and October sixteenth runs.

## 2. Architecture and entry point — 0:30

**Screen:** Rendered diagram; switch to run.sh and point to its workflow calls.

> The entry point is bash run dot sh. Sixteen Bash interfaces separate orchestration,
> collection, storage, editorial work, checking, and packaging. Focused Python
> components implement the detailed processing. The collectors discover written
> sources, YouTube videos, and podcasts. Extraction produces full text or timed
> transcripts, and JSON Lines pass records between stages. Only the store component
> accesses the persistent SQLite index. After freshness filtering, AI selects
> sources, creates briefs, and drafts articles and scripts. Checks lead to human
> review, and packaging requires an approval matching the reviewed content.

## 3. One source into a published claim — 1:15

**Screen:** Show the source quote, matching decision, brief claim, and published
article, in that order. Use the guide's search strings.

> Here is a complete claim trace. Crayon's retained source text says, “Ask for more
> and you get the full text and source link.” The source record has a stable item
> identifier and an immutable version identifier. Searching that item in the
> decisions file shows it was accepted. Brief claim zero one C zero one connects
> the claim to this exact quotation and source version. In the published article,
> the claim appears under “What source access changes.” It is explicitly attributed
> to Crayon. The article does not treat the vendor's announcement as independent
> proof of accuracy or affordability. That distinction is important: a traceable
> quotation supports what the vendor said, not every conclusion about the product.

## 4. The second run — 2:15

**Screen:** October 10 and October 16 summaries, then feedback_comparison.md.

> The October tenth run had thirty-nine eligible items from nine publishers. The
> final October sixteenth run had sixty, also from nine publishers, and produced
> another three articles and scripts. Those later drafts are separate from the
> published October tenth series. The comparison records changes in eligible
> evidence, decisions, policy, and arguments. The later collection batch shows
> two new and thirty-eight unchanged records relative to the store at that point;
> those are not the differences against October tenth. Date, sources, provider,
> and policy changed together, so this is not a controlled policy experiment.
> The later run also occurred after the supplied deadline.

## 5. Duplicate handling and recovery — 3:00

**Screen:** replay.json, then assistant brief-repair README.

> This replay re-ingested twenty-eight saved items. Every result was unchanged,
> the logical item count stayed at twenty-eight, and the latest versions remained
> identical. It is labeled as a replay, not another live collection day. Recovery
> records are also preserved. The October sixteenth briefs contained invalid
> quotations even after a bounded automated repair. The assistant's corrections
> retain before-and-after records and explain the source-attribution fixes.
> This is assisted recovery, not an unattended success. Mechanical checks can
> detect invalid references, but human interpretation still matters.

## 6. My feedback and the policy revision — 3:40

**Screen:** human_review_sample.md, then the baseline paragraph in policy v3.

> My feedback accepted sources that connected theory to practical workflows,
> provided concrete competitor-research capabilities, or described an inspectable
> multi-agent checking process. I deferred sources whose frameworks needed more
> evidence, whose speed and cost claims lacked comparisons, or whose announcements
> remained hypothetical. Policy version three implements those judgments. For
> performance claims, it asks for the same research questions and material against
> a named baseline, including preparation, checking, corrections, and actual costs.
> A useful method can still be discussed without accepting unsupported savings.
> These are editorial judgments; they do not establish that I ran that benchmark.

## 7. Tradeoff and conclusion — 4:30

**Screen:** Architecture and evaluation checklist; finish on publication links.

> The architectural tradeoff is inspectability versus operational complexity.
> Separate Bash interfaces make stages easier to inspect and replay, while Python
> handles parsing and storage. Versioned evidence preserves the reasoning trail,
> but a fresh clone needs to reconstruct the local SQLite index. Media caching
> avoids repeated transcription, while changed source media may need an explicit
> refresh. My main takeaway is that accessible evidence does not automatically
> produce reliable research: verification and maintenance are part of the workflow.
> The repository links the publications and retains the failed attempts as well
> as successful outputs. Its checklist identifies remaining review and production
> requirements rather than presenting them as completed.
