# Student editorial review

These are real student decisions. Templates and AI suggestions are not approval.

1. Read the three articles, scripts, briefs, source notes, and `review.json`.
2. Compare at least three accepted and three rejected/deferred items with your own
   judgment. `python tools/review_sample.py runs/RUN_ID` creates a worksheet without
   filling your answers. If there are too few rejected/deferred items, collect more
   genuine candidates; do not manufacture rejections.
3. Check the source passages, media timestamps, original publication dates, source
   independence, and whether the claimed benefits transfer to small businesses.
   Identify missing perspectives and whether any vendor claims became asserted facts.
4. Revise `config/editorial_policy.md` based on your findings. Keep the old version
   in the original run snapshot; start a new run to preserve a distinct version and
   outputs. Compare changed decisions and synthesis. Explain why changes matter.
5. Correct unsupported claims and document the original text, correction, evidence,
   and reason in `runs/RUN_ID/human_corrections.md`. If no factual correction was
   needed, say so honestly; a meaningful policy revision is still required.
6. Rerun `bash review/check_content.sh runs/RUN_ID > runs/RUN_ID/review.json`.

After reviewing the actual current content, **you** create `approval.json` under
the run directory. Copy the current `review_id` from `review.json` and fill:

```json
{
  "review_id": "COPY_CURRENT_REVIEW_ID",
  "decision": "approve",
  "reviewer": "YOUR NAME",
  "reviewed_at": "ACTUAL ISO 8601 UTC TIMESTAMP",
  "notes": "Your judgment, remaining limitations, and correction/review record paths"
}
```

Use `revise` if changes are needed. A change to the drafts, scripts, briefs,
evidence, decisions, or as-of date changes the fingerprint and invalidates approval.
The packaging component independently checks this even when called directly.

Automatic checks can verify structure and quoted passages. They cannot establish
that an inference is sound, a study is credible, a source is independent, or that
the article and narration make identical semantic claims. Those are your review.
