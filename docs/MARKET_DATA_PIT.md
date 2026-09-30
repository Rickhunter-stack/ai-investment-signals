# Market Integrity v2

## Confirmatory source of truth

The authoritative prospective market ledger is the Git-tracked journal in `data/market_pit/YYYY-MM.json`. SQLite tables `market_pit` and `market` are operational caches only. Confirmatory outcomes must read the JSON journal.

## Collection rule

The collector requests one month of daily data with `auto_adjust=False`, actions enabled, and stores raw close as the experimental price. Yahoo adjusted close is retained only as a control field. Each frozen row records ticker, session date, raw close, vendor adjusted close, dividend, split ratio, UTC observation time, vendor, collector, material request parameters, series type and `frozen=true`.

A returned daily bar is eligible only if the same response contains a later daily bar. The last bar in a response is never frozen. Collection covers the ten preregistered securities plus QQQ, SPY, SMH, IHI and XBI. Empty or incomplete collection fails loudly before a confirmatory journal write.

## Cadence and contiguous admission (amendment v1.3)

Confirmatory collection runs every weekday at 23:30 UTC: Monday inside the weekly radar workflow (`radar.yml`), Tuesday to Friday in the market-only workflow (`market-daily.yml`).

Each run appends every eligible session returned after the ticker's latest journal session (`admission=catchup`, with the newest as `admission=frontier`). It never inserts a session on or before that latest session, so frozen rows cannot change. `observed_at` is always the real observation time of the run.

`gap_sessions` lists the XNYS sessions still absent between two admitted rows; `gap_unbounded` marks a gap reaching beyond the one-month response window. Any outcome window crossing either marker is frozen as unavailable.

`scripts/test_outcomes_end_to_end.py` simulates several weeks of collection through the real admission path and the outcome engine, and fails if a matured horizon cannot become `measured`.

## Immutability

First observation wins for each `(ticker, session_date)`. Existing monthly-array prefixes are never rewritten. The Git append-only guard covers `data/market_pit/*.json`, weekly signals, outcomes, brief events and fundamental PIT journals.

## Outcomes

`scripts/compute_outcomes.py` reads only the Git JSON market ledger. Returns use frozen raw closes and reconstruct total return from prospectively observed dividends and splits. It never reads SQLite for confirmatory prices.

## Research provenance

Each frozen weekly snapshot embeds the qualitative research inputs used for each ticker and stores SHA-256 hashes of the complete fundamentals and signal-research inputs. Because `weekly_signals.json` is append-only protected, the exact research evidence used by every confirmatory snapshot remains auditable even when the live `signal_research.json` later evolves.

## Activation

The production schedule remains paused. Restore it only after preregistration v1.2 and Market Integrity v2 are independently reviewed, tests pass, dry-run/manual runs demonstrate no confirmatory writes, and the acceptance criteria in the pause PR are satisfied.
