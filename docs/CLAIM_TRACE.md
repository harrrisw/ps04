# Published claim trace

The published [first article](https://mingxiwang.substack.com/p/pilot-the-evidence-trail-before-automating)
states, in “What source access changes,” that Crayon describes access to underlying
text and source links. This is explicitly attributed to the vendor, with accuracy,
coverage, affordability, and implementation effort left unproven.

Follow this retained chain in `runs/20261010T052912Z-1d2e8a`:

1. [Source record](../runs/20261010T052912Z-1d2e8a/eligible.jsonl): search for
   `feed:32944883b9dff85a7148008d`. The original source is
   [Crayon's Insights API](https://www.crayon.co/blog/insights-api), published
   October 1 and retrieved October 10, 2026 according to the retained record.
2. [Immutable source text](../data/assets/c3df7e6b65257849c66ba049/b192c0ca1da12bd242489506681f276f83473000ed4152d9795eac13ccc33ed1/text.txt):
   locate “Ask for more and you get the full text and source link”.
   Version: `b192c0ca1da12bd242489506681f276f83473000ed4152d9795eac13ccc33ed1`.
3. [Editorial decision](../runs/20261010T052912Z-1d2e8a/decisions.jsonl):
   search the same item ID; its disposition is `accept`.
4. [Brief](../runs/20261010T052912Z-1d2e8a/briefs.jsonl): claim `01-C01`
   contains the item, version, and exact text locator. Claim `01-C04` combines
   this capability with NN/g's maintenance evidence into a proposed pilot rule.
   The inference is labeled separately from the capability claim.
5. [Article draft](../runs/20261010T052912Z-1d2e8a/articles/01.md) and
   [script](../runs/20261010T052912Z-1d2e8a/video_scripts/01.md) share this brief.
   [Delivered article](../deliverables/20261010T052912Z-1d2e8a/01-article.md)
   uses reader-facing source links in place of internal claim markers.
6. [Publication mapping](../runs/20261010T052912Z-1d2e8a/publication_links.json)
   connects the article to [video 01](https://youtu.be/qWxMqmFNnIw).

The [publication checks](audit/publication_checks.json) record anonymous retrieval
of all three Substack article bodies and their matching YouTube links on October
16. This confirms access and cross-links, not the independent truth of source
claims. Student source verification and final approval remain unrecorded.
