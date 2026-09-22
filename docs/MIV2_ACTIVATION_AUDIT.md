# Market Integrity v2 - Activation Audit

**Project:** `Rickhunter-stack/ai-investment-signals`  
**Audit date:** 2026-09-22  
**Status:** Market Integrity v2 active in production  
**First successful confirmatory scheduled run:** GitHub Actions run `35676622868` (Radar refresh #126)  
**Persistence PR:** #42  
**Resulting main commit:** `929ac3bd145c0c4510c074292a30c0cd40bb82f0`

## Purpose

This document records the activation state of Market Integrity v2 after the first successful end-to-end confirmatory run.

It is documentary only. It does not change the preregistered methodology, the confirmatory universe, the scoring model, any frozen snapshot, any market observation, or any outcome.

## 1. Activation result

The first official scheduled confirmatory run completed successfully.

The production chain executed as intended:

```text
schedule
  -> automation credential preflight
  -> confirmatory market collection
  -> fundamentals refresh
  -> fundamentals PIT freeze
  -> weekly Signal Score freeze
  -> prospective outcome evaluation
  -> market journal validation
  -> append-only verification
  -> protected automation PR
  -> required integrity checks
  -> protected merge to main
  -> deployment
```

No branch-protection bypass was introduced by the MIv2 implementation.

## 2. Confirmatory market journal

The first production run admitted 15 frozen market observations:

### Confirmatory securities

- NVDA
- AVGO
- QCOM
- MU
- GOOGL
- AMZN
- ADI
- MDT
- ISRG
- GH

### Benchmarks and sensitivity series

- QQQ
- SPY
- SMH
- IHI
- XBI

All 15 records were written prospectively by the scheduled run with run provenance, source/collector metadata and frozen integrity fields.

The admitted journal session was `2026-09-18`.

The global vendor boundary frozen into the weekly snapshot was `2026-09-21`.

This difference is intentional. Under the completed-session rule, the newest daily bar returned by the same vendor response is used as a conservative frontier but is not itself admitted to the journal because there is no strictly later daily bar in that response proving completion.

## 3. T0 state after activation

For each of the 10 confirmatory securities, the first complete weekly snapshot stores:

```text
t0_after_session = 2026-09-21
```

A valid T0 must therefore be the first prospectively admitted common security/benchmark session strictly after `2026-09-21`.

At activation time, no such row yet existed in the immutable market journal.

Therefore:

- no T0 anchor was created;
- `data/outcomes_v1.json` correctly remained empty;
- this is expected behavior, not missing output.

The first T0 anchors will be created only when a later official scheduled run prospectively admits an eligible common session after the frozen boundary.

## 4. Clarification: 2026-09-14 snapshot

The historical snapshot dated `2026-09-14` remains frozen and unchanged.

It contains 33 ticker entries, but all `signal_score` values are null and `top3` is empty.

It should therefore be described as an **incomplete historical snapshot**, not as a complete scored confirmatory observation.

Under the preregistered missing-data rules, it remains visible in the historical ledger but does not contribute to score-stratified confirmatory analyses that require a complete Signal Score.

For the current `weekly-v1.0` experiment, the first complete scored confirmatory cohort is therefore the snapshot captured on `2026-09-22`.

This clarification does not rewrite, delete or reinterpret the frozen 2026-09-14 object.

## 5. Clarification: snapshot universe versus confirmatory universe

`data/weekly_signals.json` may contain ticker entries outside the v1 confirmatory universe.

The snapshot dated `2026-09-22` contains 33 ticker entries in total, while the preregistered confirmatory universe remains strictly limited to:

```text
NVDA, AVGO, QCOM, MU, GOOGL, AMZN, ADI, MDT, ISRG, GH
```

Only these 10 securities are eligible for the v1 confirmatory analysis.

Other ticker entries are operational, exploratory or seed-universe records. They must not be mixed into v1 confirmatory statistics, score buckets, hit rates, rank correlations, baselines or outcome summaries unless a future dated protocol explicitly creates a new prospective universe.

## 6. First complete scored cohort

The first complete scored confirmatory snapshot was captured on `2026-09-22`.

Its frozen top three were:

| Ticker | Signal Score |
| --- | ---: |
| QCOM | 82.25 |
| AVGO | 70.20 |
| MDT | 69.00 |

These values are hypotheses frozen prospectively. They are not evidence of predictive success.

Their value can only be assessed from future prospectively admitted T0 and outcome observations.

## 7. Append-only verification

Activation preserved existing frozen history.

Verified behavior includes:

- the 2026-09-14 weekly snapshot remained unchanged;
- the 2026-09-22 snapshot was appended;
- the fundamentals PIT ledger preserved its previous prefix and appended new frozen observations;
- the market PIT journal was created prospectively rather than backfilled;
- the outcome ledger was not populated without an eligible prospective T0.

Future corrections to historical facts or interpretations must be represented prospectively and must not rewrite frozen records.

## 8. Automation and protected persistence

The scheduled run persisted its outputs through an automation branch and pull request rather than a direct push to protected `main`.

The automation PR passed the required repository integrity checks before merge.

Non-confirmatory `push`, `pull_request` and `workflow_dispatch` executions remain unable to create confirmatory market rows, weekly freezes or outcomes.

The post-merge push run therefore remains operational only and does not duplicate confirmatory observations.

## 9. Cron timing

The official workflow is configured for:

```text
30 23 * * 1
```

GitHub scheduled workflows are not guaranteed to start exactly at the requested minute.

MIv2 therefore relies on the real `observed_at` timestamp and XNYS/calendar validation rather than assuming execution at exactly 23:30 UTC.

A delayed run must still satisfy all vendor-frontier and completed-session integrity checks. If those conditions are not satisfied, the run is expected to fail closed rather than manufacture an earlier eligible observation.

## 10. Scope freeze after activation

With the first successful confirmatory run completed, Market Integrity v2 is considered operational.

From this point:

- no MIv2 methodology change should be made merely to improve future measured performance;
- no frozen record should be edited;
- no confirmatory-universe ticker should be added or removed based on subsequent returns;
- implementation changes should be limited to genuine bugs, security issues, reproducibility failures or explicitly versioned future protocols;
- Research Pipeline v2 remains a separate research-development project and must not be silently mixed into `weekly-v1.0`.

## 11. Activation conclusion

The experiment has now moved from infrastructure validation to prospective observation.

The relevant next milestones are data milestones rather than activation milestones:

1. first valid prospective T0 anchors;
2. first M+1 outcomes;
3. later M+3, M+6 and M+12 outcomes;
4. accumulation of sufficient observations for the preregistered descriptive analyses and baselines.

**Market Integrity v2 measures whether the frozen signals were right. Its historical record must remain capable of proving that they were wrong.**
