# Brief ingestion v1

This layer turns each selected ChatGPT daily-brief item into one prospective `brief-event-v1` record.

## Contract

- One selected news item becomes one event. Do not split an article merely to create more signals.
- Record only information available at `captured_at`.
- `factual_summary` must stay factual; interpretation belongs in classification, direction, horizon and scores.
- Every event requires at least one HTTP(S) source.
- Events are frozen on ingestion and existing events are never edited, deleted or reordered.
- A repeated story still becomes a new dated event only when it is materially useful; `story.relation` is reserved for the next deduplication layer.
- No event is allowed to change `weekly_signals.json` directly in v1.

## ChatGPT daily brief flow

1. Research and select exactly five useful daily items as usual.
2. Produce the human-readable French brief.
3. For investment-relevant items, map the information to `brief-event-v1` without inventing tickers or scores.
4. Validate the records with `scripts/validate_brief_events.py` / `scripts/ingest_brief_events.py`.
5. Append them to `data/brief_events/YYYY-MM.json`.

The journal is the prospective source of truth for future story clustering, theses, criticality scoring and outcome measurement.
