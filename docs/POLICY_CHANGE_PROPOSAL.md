# Policy revisions and student feedback

The first completed AI selection used policy version 1, saved under
`runs/20261010T052041Z-15fd8c/config/editorial_policy.md`. It accepted three written
items and rejected or deferred every audio/video item. Consequently, the pipeline
correctly refused to create unsupported briefs.

Several media deferrals demanded performance-study methods even where the useful
claim would be an attributed practitioner observation or a limitation. That is a
mismatch between the evidence and the kind of claim being considered. The proposed
version 2 makes the distinction explicit: interviews may support attributed
experience and questions to investigate; they do not establish effectiveness,
accuracy rates, ROI, or broad generalizations. It also distinguishes actual evidence
of republication from unsupported suspicion about an earlier recording date.

Version 2 was proposed by the coding assistant while debugging editorial behavior,
before the student's feedback. Its October 10 results do not count as a rerun caused
by later student feedback.

On October 16 the student supplied judgments on three accepted and three deferred
sources, retained in the [six-item review record](../runs/20261010T052912Z-1d2e8a/human_review_sample.md)
and [submission](../SUBMISSION.md). Version 3 implements those judgments: prefer
inspectable workflows and concrete capabilities, avoid treating multi-agent
agreement as verification, require worked baselines for speed/cost claims, and
inspect survey methods before drawing revenue or small-business conclusions.

October 16 runs snapshot version 3. The completed live-run comparison, when
available, distinguishes changed evidence from changed policy and model behavior;
it cannot attribute every editorial change to policy alone. Source/audio
verification and final human approval have not been reported.
