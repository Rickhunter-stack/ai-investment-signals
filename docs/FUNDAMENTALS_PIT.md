# Fundamentals point-in-time ledger v1

## Problem

`data/fundamentals.json` is a refreshable dashboard input. The collector downloads standardized Yahoo/yfinance statements on every run and rewrites the file. It therefore cannot itself prove what fundamental values the project had observed at an earlier T0.

The weekly snapshot already embeds its contemporaneous fundamental inputs, which protects existing frozen scores. This layer adds a separate longitudinal research ledger for future auditing and outcome/baseline work.

## Ledger

`scripts/freeze_fundamentals_pit.py` appends observations to:

`data/fundamentals_pit/YYYY-MM.json`

Each observation records:

- permanent observation ID;
- ticker;
- `observed_at`;
- source and source collection timestamp;
- fiscal year represented by the collector's `latest` record;
- the metrics actually observed;
- `frozen: true`;
- schema version `fundamentals-pit-v1`.

A later provider revision creates a later observation. It never replaces the old one.

## Metrics v1

- revenue
- OCF
- CAPEX
- FCF
- CAPEX / OCF
- FCF margin
- FCF/share
- ROIC
- FCF yield
- available-history FCF CAGR
- available-history FCF/share CAGR

## Important limitation

This is **observation-time integrity**, not perfect filing-time integrity.

Yahoo/yfinance standardized annual statements do not reliably expose the exact public filing timestamp for every value. Freezing the value when this project first observes it prevents future contamination of our own history, but it does not prove that the value first became public at that moment.

For stronger future work, primary SEC/EDGAR filings should provide `filed_at`, fiscal period and accession/form metadata. That should be a new source/version rather than rewriting v1 observations.

## No backfill

Do not populate this ledger from previously downloaded historical statements and call them prospective observations. The ledger starts when this code becomes operational.
