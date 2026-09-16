# Daily brief ingestion v1

After the human-readable ChatGPT brief, each investment-relevant selected item may be encoded as one `brief-event-v1` object and appended prospectively to `data/brief_events/YYYY-MM.json`.

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
