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


## Safe GitHub write protocol

When ingestion is performed through the GitHub connector, the monthly journal must be updated with optimistic concurrency rather than from a truncated preview:

1. Read the complete `data/brief_events/YYYY-MM.json` with the repository file-content operation (`fetch_file`), and retain its current blob SHA.
2. Parse the complete JSON array and validate the frozen history before changing anything.
3. Build and story-classify only the new events. Reject any event without a reliable timezone-aware `published_at`.
4. Append new events in memory. Never edit, delete, reorder, normalize, or reserialize historical event objects semantically.
5. Run the same journal and append-only validation rules before writing.
6. Replace the repository file only with the complete validated array and pass the previously fetched blob SHA to the file update operation. The SHA is an optimistic-concurrency guard: if the file changed after the read, the write must fail rather than overwrite concurrent history.
7. Re-read the file after the write and verify that all previous event IDs are still present unchanged and that every new event ID appears exactly once.
8. If a complete file read, SHA-guarded update, validation, or verification is unavailable, fail closed and report ingestion failure. Never reconstruct the journal from a truncated response.

Do not use generic page previews or truncated search/fetch output as the source for a journal replacement. The repository file-content read is the authoritative path for connector-based ingestion.
