# Daily brief ingestion v1

After the human-readable ChatGPT brief, each investment-relevant selected item may be encoded as one `brief-event-v1` object and written prospectively to one immutable daily journal `data/brief_events/YYYY-MM-DD.json`.

Rules:
- record only information available at `captured_at`;
- keep `factual_summary` factual and put interpretation in classification/direction/scores;
- require at least one reliable HTTP(S) source;
- use only implicated companies/tickers; empty arrays are acceptable when no listed company maps cleanly;
- score importance, novelty, confidence and execution risk from 0-100, with 100 = highest execution risk;
- use `pricing_status: uncertain` when evidence is insufficient;
- until story clustering is implemented, use `story_id: null` and `relation: NEW`; do not guess prior relations;
- until the thesis registry is implemented, keep `thesis_ids` empty; a candidate statement may be recorded but never rewritten later;
- `frozen` is always true;
- never edit, delete or reorder an existing event;
- do not backfill briefs produced before activation;
- this layer does not modify `signal_research.json` or `weekly_signals.json`.

Run `python -m unittest discover -s scripts -p 'test_brief*.py'` before activation.


## Daily immutable journal protocol

The legacy monthly journals (for example `data/brief_events/2026-09.json`) remain frozen source history and are never migrated, split, edited, deleted or reordered.

For every new brief after activation:
1. Read all available historical journals under `data/brief_events/` for story comparison. Both legacy `YYYY-MM.json` and daily `YYYY-MM-DD.json` files are valid history.
2. Build and validate only events with a reliable timezone-aware `published_at` not later than `captured_at`.
3. Story-classify each new event against the combined frozen history.
4. Write the day's events only to `data/brief_events/YYYY-MM-DD.json`.
5. If that daily file does not exist, create it as a JSON array. If it already exists, fetch its complete contents and SHA and append only to it using optimistic concurrency.
6. Never rewrite a legacy monthly journal to ingest a new brief.
7. Re-read the daily file after writing and verify that previous entries are unchanged and every new event ID occurs exactly once.
8. Fail closed if validation, complete reading of an existing daily file, SHA-guarded update, or post-write verification is unavailable.

Daily journals are source-of-truth files, not temporary shards. Aggregated views may be derived later, but must never replace or mutate these frozen source journals.
