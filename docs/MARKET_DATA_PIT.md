# Point-in-time market data convention

## Purpose

Future M+1 / M+3 / M+6 / M+12 evaluation needs prices that are comparable and cannot silently change after T0.

## Experimental source of truth

`market_pit` is the prospective market ledger. The legacy `market` table remains temporarily for dashboard compatibility and must not be used for future outcome calculations.

## Price convention

Securities and benchmarks are collected with the same `yfinance` convention: `auto_adjust=True` with repair enabled. The stored field is named `adjusted_close`.

This removes the previous inconsistency where securities used raw Close while URTH used an adjusted series.

## Immutability

`market_pit` uses `(ticker, date)` as its primary key and collection uses `INSERT OR IGNORE`. Once the first observation for a ticker/date is stored, a later provider revision cannot overwrite it.

Each row records `observed_at`, `source`, and whether it is a `security` or `benchmark`.

## Benchmarks

SPY and QQQ are collected prospectively. The deterministic rule assigning a benchmark to each security will be frozen later in `PREREGISTRATION.md`; this PR intentionally does not choose the better-looking benchmark after outcomes are known.

## Important limitation

Adjusted-close histories supplied by a data vendor can themselves embed later corporate-action knowledge. Freezing the first value observed prevents subsequent rewrites in our database, but this is not a perfect institutional-grade point-in-time market-data feed. The limitation must remain documented when interpreting results.

## T0 convention still to preregister

This change does not yet decide whether an event published intraday is evaluated from publication-time price, next open, same close, or next close. That rule must be specified prospectively before outcome measurement begins.
