# Structured output contract for the daily ChatGPT brief

After the human-readable brief, investment-relevant selected items should be encoded as `brief-event-v1` objects for ingestion.

Rules for the automation:

- Use the actual run time for `captured_at` and the source publication time for `published_at` when known.
- Use `FACT` for directly documented information, `WEAK_SIGNAL` for a sourced early pattern, and `HYPOTHESIS` only for an explicit interpretation.
- `factual_summary` must not contain the investment conclusion.
- Include only companies/tickers actually implicated by the item. Empty arrays are allowed when no listed company maps cleanly.
- Scores are 0-100 and express importance, novelty, confidence in the classification, and execution risk (100 = highest risk).
- `pricing_status` may be `uncertain`; do not pretend to know what is priced.
- Until story clustering is implemented, new stories use `story_id: null` and `relation: NEW`. Do not guess a prior story relation.
- Until the thesis registry is implemented, `thesis_ids` stays empty. `statement` may contain a concise candidate thesis but must not rewrite any historical event later.
- `frozen` is always true.
- Never alter or delete an existing journal event.

This contract deliberately separates observation capture from later deduplication, thesis building and scoring.
