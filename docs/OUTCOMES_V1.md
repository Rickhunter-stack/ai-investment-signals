# Outcomes engine v1

This engine implements the frozen rules in `PREREGISTRATION.md` without changing weekly snapshots.

## Append-only model

`data/outcomes_v1.json` is an immutable journal. A weekly observation first receives a T0 anchor. M+1, M+3, M+6 and M+12 are appended only after their calendar target is reached and a common security/benchmark trading date exists in `market_pit`.

Existing outcome rows are never recomputed or overwritten.

## Confirmatory universe and benchmark

QQQ: NVDA, AVGO, QCOM, MU, GOOGL, AMZN, ADI.

SPY: MDT, ISRG, GH.

Only frozen weekly observations created on/after the preregistration/integrity start (2026-09-17) are eligible. The 2026-09-14 legacy snapshot remains visible in weekly history but is not converted into a confirmatory outcome.

## Returns

For each horizon, the first common US trading date on or after the calendar target is used for security and benchmark. Returns use immutable adjusted-close observations from `market_pit`.

`excess_return = security_return - benchmark_return`

M+6 remains the primary confirmatory endpoint. Other horizons are secondary.

## Pending horizons

Pending horizons are deliberately not written as mutable placeholders. Nothing is appended until the target date has passed and both prices exist. This keeps the journal strictly append-only.

## Known limitation

The preregistration describes "after relevant US regular-market close". v1 operationalizes that daily convention with a conservative 20:00 UTC cutoff. This is not an intraday execution model. A future protocol version may replace this only prospectively.

The engine does not yet compute aggregate hit rates, score buckets, Spearman correlation or ablation baselines. Those are downstream analyses.
