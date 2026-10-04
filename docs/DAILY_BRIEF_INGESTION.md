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


## Unified research entry point

The preferred daily research workflow is defined in `docs/UNIFIED_DAILY_BRIEF_V1.md`. It replaces separate overlapping daily AI-sector and recurring-company briefs with one evidence pass. This ingestion document remains authoritative for the write path and frozen-event integrity rules.


## Ingestion execution and error reporting

Prefer the repository's own ingestion and validation scripts whenever the execution environment can run them. The canonical path is:

1. construct candidate `brief-event-v1` objects;
2. run story classification;
3. ingest with `scripts/ingest_brief_events.py`;
4. run `scripts/validate_brief_events.py`, the brief-event tests, and `scripts/check_append_only_git.py`;
5. only then commit/push and open a pull request.

If the environment cannot execute the repository scripts, do not emulate a successful validated ingestion silently. Either use the GitHub connector only for a fully auditable write path or fail closed.

When any write, validation, commit, push, or PR creation step fails, report the raw error message exactly when available, together with the step that failed. Do not replace an unknown cause with an inferred explanation such as permissions, branch protection, or a safety control unless the returned error explicitly says so.


## Definition of a fully auditable connector write path

A direct GitHub-connector write is considered fully auditable only if all of the following are true before merge:

1. the candidate journal is created on a non-`main` branch;
2. `scripts/validate_brief_events.py` runs successfully against that branch state;
3. the brief-event test suite runs successfully;
4. `scripts/check_append_only_git.py` confirms append-only integrity against `main`;
5. the pull request contains the classifier audit required by `STORY_DEDUP_V1.md`;
6. required CI checks pass before merge.

If the current environment cannot execute these repository checks itself, it may still create the branch/file/PR, but the ingestion must be reported as **pending validation**, not successful, until the pull-request checks have passed. If no repository validation can be obtained, fail closed and do not merge.


## Freshness alert

`.github/workflows/brief-freshness.yml` runs daily at 12:00 UTC and fails when the most recent `captured_at` in `main` is more than 24 h old (`scripts/check_brief_freshness.py`). On failure it opens, or comments on, a GitHub issue titled "Brief journal missing". A day with no investment-relevant event legitimately triggers it; close the issue with that explanation.
