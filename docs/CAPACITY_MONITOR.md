# Capacity Monitor v0.1 (AI CAPACITY)

**SHADOW MODEL — EXPERIMENTAL — NON SCORING.** An independent research indicator of the AI physical buildout. It never enters the Signal Score, the weekly snapshots, the market journal, the outcomes or T0 anchoring. There is no arrow from Capacity to the Signal Score.

`method_version: capacity_monitor_v0.1`. Frozen definitions: `config/capacity/definitions_capacity_monitor_v0.1.json`. That file is immutable once merged; any change creates a new file and a new method version.

## Why it lives in this repository

Keeping it in the same repository but fully separated (own data, workflow, method and protocol) allows a later, exploratory analysis of `SignalScore(T0)` × `CapacityState(T0)` × `Outcome(M+6)`. Any such finding is discovered, not built into the score.

## Methodological wall and session separation

```
WEEK N
  Session A: company research -> novelty / pricing_headroom / execution_risk -> signal_research.json
  Monday run: weekly Signal snapshot N frozen (captured_at + research SHA-256)
  ================= methodological wall =================
  Session B: Capacity research -> observations -> Capacity snapshot N -> AI CAPACITY
```

- **Session A (weekly signals)** may use filings, IR, press, etc., but **never** `data/capacity/**`, Capacity snapshots, the AI CAPACITY panel, AS or E-C-T-D-F. A primary source may appear independently in both researches; using the Capacity analysis as a source or as scoring context is forbidden. `scripts/validate_signal_research_isolation.py` fails CI when `signal_research.json` cites Capacity artefacts.
- **Session B (Capacity)** is a different session. It works only after the weekly freeze.
- The wall protects snapshot N against Capacity N. It does **not** protect the research for N+1 against what was learned from Capacity N; only session separation does. This limitation must be stated in any later analysis.

Each observation records `weekly_snapshot_date`: the latest frozen weekly snapshot captured before its `observed_at`. Each Capacity snapshot records `weekly_snapshot_date`, `weekly_snapshot_captured_at`, `weekly_research_sha256` and `capacity_snapshot_captured_at`. The validator checks them against `data/weekly_signals.json`, so the order is auditable afterwards.

## Point-in-time rules

- `source.published_at` (when the source was published) and `observed_at` (when the monitor ingested it) are different. `observed_at` is set by `scripts/append_capacity_observations.py` at ingestion time and is never backdated.
- Data gathered before the module existed is ingested with `--historical-seed` (`historical_seed: true`). Its `observed_at` is still the ingestion time: it builds the initial state but is not a prospective observation from before activation.
- Observations are append-only (`data/capacity/observations/YYYY-MM.json`). A level change, a delay or a cancellation is a new observation. A correction is a new observation with `supersedes`; the old one keeps counting for any date before the correction.
- "What the monitor knew at t" = latest non-superseded observation per key among those with `observed_at <= t`.
- `data/capacity/snapshots.json` is append-only, one snapshot per weekly period and method. Each snapshot must be exactly reproducible from the journal (checked by `scripts/validate_capacity.py`).
- A later method (for example v0.2 of AS or E-C-T-D-F) is a new definitions file and version. It never rewrites v0.1 snapshots; recomputations on past dates are exploratory and kept separate.

## Definitions v0.1

**Commitment ladder.** C0 announcement only · C1 site/land option/grid request · C2 advanced project (secured site, significant permits, grid or procurement agreement) · C3 economic commitment (FID, firm financing, binding contract, irreversible spending) · C4 construction or installation started · C5 energized/commissioned and operational · X cancelled/abandoned (never erases history) · UNKNOWN when evidence is insufficient to assign a level. A project moves up only with evidence matching the level's criterion.

**C (Supply Commitment)** is derived: raw GW per level, Committed = C3+C4+C5, Operational = C5. No probability weights in v0.1: they will be estimated later from observed transitions (P(C5 | Cn)).

**Effective capacity** = capacity physically usable for AI compute, limited by the binding link whose availability is documented. v0.1: C5 operational capacity plus C3/C4 capacity with documented critical dependencies (`dependencies_documented` + evidence URLs). Only the canonical unit `GW_IT` (MW_IT converted) is summed. GPU, HBM, network or power quantities are never converted: if nothing can be summed, the value is `null`, never estimated.

**Buildout 2026-2030** = capacity available in each vintage (online year <= y, still within useful life). Depreciation: full retirement at the end of `expected_useful_life_years`; unknown lives are kept and reported as `depreciation_unknown_gw`.

**Absorption Stress** `AS[y][s] = effective[y] / independent_demand[y][s]`, s ∈ {bear, base, bull}. `null` when either side is missing, units are not comparable, demand <= 0, or several demand series exist for one scenario/year without a declared reference. No automatic threshold: AS is a stress ratio, not a crash indicator.

**E (Supply Elasticity)**: qualitative LOW / MEDIUM / HIGH per supply-chain node, with justification and source. **T (Time-to-Supply)**: derived from project dates (realized commitment -> commissioning delay, expected committed GW per vintage). **D (Demand Reality Gap)**: expressed by AS. **F (Financing Independence)**: qualitative HIGH / MEDIUM / LOW / UNKNOWN, with justification, source and mandatory documented relations. The five dimensions are never aggregated into a score.

## Files and commands

| Path | Role |
|---|---|
| `scripts/append_capacity_observations.py drafts.json [--historical-seed]` | Session B ingestion (sets ids, `observed_at`, wall reference) |
| `scripts/compute_capacity_snapshot.py` | Freezes the snapshot of the current weekly period (writes only with `CAPACITY_WRITE=1`) |
| `scripts/validate_capacity.py` | Journal, PIT, wall and reproducibility checks |
| `.github/workflows/capacity-monitor.yml` | Sunday 12:00 UTC, persists through a protected PR, touches only `data/capacity` |
| `capacity.js` | AI CAPACITY overlay; reads only `/data/capacity/snapshots.json` |

Capacity checks gate pull requests and pushes but never the confirmatory scheduled radar run. Isolation tests (`scripts/test_capacity_isolation.py`) prove that the pipeline writes only under `data/capacity/` and that the Signal protocol code never references the module.
