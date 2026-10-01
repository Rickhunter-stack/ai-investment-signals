# Research Protocol v2.0 (DRAFT)

**Status:** DRAFT under audit; integral part of `PREREGISTRATION_V2.md`. Frozen at merge; changes afterwards only through a dated, versioned amendment that applies prospectively.
**Drafted:** 2026-10-01
**Governs:** the three qualitative components of the `weekly-v1.0` Signal Score (novelty, pricing_headroom, execution_risk) stored in `data/signal_research.json`.

## 0. Why this protocol exists

Three of the five score components are sourced judgments written with an LLM. With 33 companies instead of 10, the main risk to v2 is not missing data but unequal and drifting judgment: some companies researched more often or more deeply than others, a model or prompt change mid-stream, or a pipeline that implicitly rewards producing novelty every week. If that happens, v2 measures the analyst's attention, not the model. This protocol fixes the procedure before any v2 observation exists.

## 1. Scope — DECISION REQUIRED

- **Option A (recommended): one procedure for all 33 tickers**, including the 10 v1 tickers, from the v2 activation date. A single research file, a single procedure. Consequence: the process generating v1 research inputs changes mid-experiment. v1 never froze its research procedure (v1 §13), so this is not a change to a v1 confirmatory rule, but it must be recorded as a dated note in `PREREGISTRATION.md`, and v1 results must be reportable before/after that date.
- **Option B: v2-only.** Two research streams coexist for the 10 common tickers. Avoids touching v1 inputs, but doubles their research load and produces two scores for the same company in the same week.

## 2. Model and prompt

1. The research prompt is a versioned file, `config/research_prompt_v2.md` (to be written before merge), identified by its SHA-256.
2. Every entry records the model identifier actually used and the prompt SHA-256.
3. **Model change policy:** the model may change only through a dated changelog entry in this file, effective from a given weekly snapshot, and applied to all tickers from that snapshot onward. Two models are never mixed within one weekly cross-section. Results are reportable by model period as a sensitivity analysis.
4. A prompt change is a new prompt version, under the same rules.

## 3. Admissible sources

Hierarchy (from `docs/RESEARCH_ENGINE_V2.md`):

1. regulatory filings and official results;
2. primary customer or supplier confirmation;
3. earnings calls and investor presentations;
4. reputable independent reporting;
5. estimates, flagged as such;
6. hypotheses, which may motivate a review but never justify a score on their own.

Every cited source must have been published before the entry's `date`, and the entry's `date` must not be later than the snapshot cutoff that uses it.

**Excluded sources:**

- outputs of the Capacity Monitor (already enforced by `scripts/validate_signal_research_isolation.py`);
- any outcome, realized return or performance computed by this project (`outcomes_v1.json`, `outcomes_v2.json`, monthly reports, dashboards);
- social media posts and anonymous forums;
- opinions produced by another AI assistant.

**Blinding:** the researcher (human or LLM) does not consult this project's outcome journals or post-T0 performance of earlier snapshots when producing an entry. The research prompt states this explicitly.

## 4. Review calendar and comparable budget

1. **Scheduled review:** each ticker is fully reviewed every 4 weeks, on a fixed rotation assigned mechanically by seed order (ticker position modulo 4 → week of the cycle). About 8 or 9 tickers per week.
2. **Event-triggered review:** an additional review is performed, for every ticker alike, after a prespecified material event:
   - publication of quarterly or annual results;
   - announcement of an acquisition, divestiture or merger;
   - guidance change announced by the company;
   - regulatory decision on a product (e.g. FDA approval or rejection, major clearance);
   - Form 8-K, or the issuer's equivalent, reporting a material agreement, impairment or executive departure.

   An event outside this list does not trigger a review.
3. **Equal budget per review:** same prompt, one research pass per ticker, between 2 and 8 cited sources, a novelty lookback window of 90 days. No extra passes or deeper dives for tickers judged "interesting".
4. Every review is logged with a `review_id`, its type (`scheduled` or `event:<type>`) and its date, including reviews that change nothing.

## 5. Unchanged score is a valid result

The absence of material new information must produce exactly the same score as the previous entry. This is the expected default, not a pipeline failure.

1. A review with no material change produces a **reaffirmed** entry: same score, new `date`, `reaffirmed: true`, a rationale stating "no material change since <previous date>", and the sources actually checked during the review.
2. **A score may change only if** the rationale cites at least one source published after the previous entry's date and explains why it is material.
3. The research prompt explicitly instructs that reaffirmation is the default, and that finding nothing new is an acceptable answer.
4. The proportion of reaffirmed entries is reported each month, with no target. A high proportion is not an anomaly.

## 6. Validity and missing data

1. An entry remains valid for 35 days after its `date` (existing rule of `docs/WEEKLY_SIGNALS.md`). The 4-week rotation keeps every ticker inside that window, with a 7-day margin.
2. After 35 days without a new or reaffirmed entry, the component is missing, the Signal Score is null and the observation is not v2-eligible. It is never imputed or carried forward beyond 35 days.
3. A missed review is reported as such. It is never backfilled later with a back-dated entry.
4. An entry is never edited after it has been used by a frozen snapshot. A correction is a new entry with a later date.

## 7. Required provenance fields

In addition to the existing `score`, `date`, `rationale` and `sources` fields:

| Field | Content |
|---|---|
| `research_protocol` | `research-v2.0` |
| `review_id` | unique identifier of the review |
| `review_type` | `scheduled` or `event:<type>` |
| `model` | model identifier actually used |
| `prompt_sha256` | SHA-256 of the prompt file |
| `reaffirmed` | `true` if the score is unchanged for lack of material new information |
| `previous_date` | date of the previous entry for this component, or `null` |

A validator must reject a v2 entry missing any of these fields (activation condition 4 of `PREREGISTRATION_V2.md`).

## 8. Scoring anchors — to be completed before merge

The research prompt will define anchors at 0, 25, 50, 75 and 100 for each component, for example:

- **novelty:** 0 = no material event in the lookback window; 50 = a material event that extends a known trend; 100 = a material event that changes the company's position in its value chain;
- **pricing_headroom:** 0 = the event is fully known to the market and discussed in consensus; 100 = material and verifiable, but largely absent from public discussion;
- **execution_risk:** 0 = a proven, already-recurring capability; 100 = depends on an unproven technology, approval or capacity.

The anchors are fixed before the first v2 entry. Existing v1 entries are not rescored retrospectively.

## 9. Audit

1. Each month, a random sample of 10 % of the month's v2 entries (at least 3) is checked by the project owner: sources exist, were published before the entry date, and support the rationale. Results are recorded in a dated audit log.
2. An entry that fails the audit is not edited. The failure is recorded, and the next review produces a new entry.
3. Exploratory option: an independent second scoring of a sample by a different model or person, to measure inter-rater agreement, reported separately and never used as a score input.

## Changelog

| Version | Date | Change |
|---|---|---|
| v2.0 (draft) | 2026-10-01 | Initial draft. |
