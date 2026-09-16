# Brief Events v1

`data/brief_events/YYYY-MM.json` is the prospective, append-only source of truth for facts and weak signals extracted from daily briefs.

## Principle

An event records only what was known at capture time. Once committed with `frozen: true`, it must never be edited, deleted or reordered to improve a later result. Corrections, confirmations, accelerations, deterioration and contradictions are new events.

The event is the atomic unit. Several events may later feed one story or thesis, and one event may affect several companies.

## Classification

- `FACT`: directly supported factual development.
- `WEAK_SIGNAL`: sourced observation whose investment significance is not yet established.
- `HYPOTHESIS`: explicit interpretation that must not be presented as fact.

`story.relation` is one of `NEW`, `REPEAT`, `CONFIRM`, `ACCELERATE`, `DETERIORATE`, `CONTRADICT`, `RESOLVE`. This PR stores that relation but does not attempt automatic deduplication yet.

Scores `importance`, `novelty`, `confidence` and `execution_risk` are integers from 0 to 100. They are capture-time metadata, not an investment recommendation or a future-performance label.

`pricing_status` is one of `not_priced`, `partially_priced`, `priced`, `uncertain`.

## Validation

Run:

```bash
python scripts/validate_brief_events.py
python -m unittest scripts/test_brief_events.py
```

The validator checks the monthly journals. `validate_append_only(previous, current)` provides the guard that ingestion and CI can use to prove that the previous frozen prefix is byte-for-byte equivalent at the parsed-event level before accepting appended events.

## Scope of v1

This slice intentionally does not change `weekly_signals.json`, scoring, thesis generation, dashboard UI, Vercel or the market/fundamental collectors. The next layer can ingest real daily briefs into this journal and then implement story-level deduplication against genuine prospective data.
