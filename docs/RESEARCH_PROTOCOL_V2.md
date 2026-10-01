# Research Protocol v2.0 (DRAFT)

**Status:** DRAFT under audit; integral part of `PREREGISTRATION_V2.md`. Frozen at merge; changes afterwards only through a dated, versioned amendment that applies prospectively.
**Drafted:** 2026-10-01
**Governs:** the three qualitative components of the `weekly-v1.0` Signal Score (novelty, pricing_headroom, execution_risk) stored in `data/signal_research.json`.
**Research prompt and scoring anchors:** `config/research_prompt_v2.md` (integral part of this protocol).

## 0. Why this protocol exists

Three of the five score components are sourced judgments written with an LLM. With 33 companies instead of 10, the main risk to v2 is not missing data but unequal and drifting judgment: some companies researched more often or more deeply than others, a model or prompt change mid-stream, or a pipeline that implicitly rewards producing novelty every week. If that happens, v2 measures the analyst's attention, not the model. This protocol fixes the procedure before any v2 observation exists.

## 1. Scope

One procedure for all 33 tickers of the v2 universe, **including the 10 v1 tickers**, from the v2 activation snapshot onward (decision of 2026-10-01). A single research file and a single procedure.

For the 10 v1 tickers, this changes the process that generates v1 qualitative inputs. v1 never froze its research procedure (v1 §13), so no v1 confirmatory rule changes; the change date is recorded in v1 by amendment v1.4, no past score is modified, and v1 analyses report the periods before and after the change as a sensitivity analysis.

## 2. Model and prompt

1. The research prompt is the versioned file `config/research_prompt_v2.md`, identified by its SHA-256.
2. Every entry records the model identifier actually used and the prompt SHA-256.
3. **Model change policy:** the model may change only through a dated changelog entry in this file, effective from a given weekly snapshot, and applied to all tickers from that snapshot onward. Two models are never mixed within one weekly cross-section. Results are reportable by model period as a sensitivity analysis.
4. A prompt change, including any change to the anchors, is a new prompt version under the same rules.

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

**Blinding:** the researcher (human or LLM) does not consult this project's outcome journals or post-T0 performance of earlier snapshots when producing an entry. The research prompt states this explicitly. Public market information available at the cutoff (valuation level, consensus, coverage) remains admissible for pricing_headroom.

## 4. Review calendar and comparable budget

1. **Scheduled review:** each ticker is fully reviewed every 4 weeks, on a fixed rotation assigned mechanically by seed order (ticker position modulo 4 → week of the cycle). About 8 or 9 tickers per week.
2. **Event-triggered review:** an additional review is performed, for every ticker alike, after a prespecified material event:
   - publication of quarterly or annual results;
   - announcement of an acquisition, divestiture or merger;
   - guidance change announced by the company;
   - regulatory decision on a product (e.g. FDA approval or rejection, major clearance);
   - Form 8-K, or the issuer's equivalent, reporting a material agreement, impairment or executive departure.

   An event outside this list does not trigger a review.
3. **Equal budget per review:** same prompt, one research pass per ticker, between 1 and 8 cited sources, a novelty lookback window of 90 days. No extra passes or deeper dives for tickers judged "interesting".
4. Every review is logged with a `review_id`, its type (`scheduled`, `event:<type>` or `baseline`) and its date, including reviews that change nothing.

## 5. Score changes and reaffirmation

### 5.1 An unchanged score is a valid result

The absence of material new information must produce exactly the same score as the previous entry. This is the expected default, not a pipeline failure.

A review with no admissible reason to change produces a **reaffirmed** entry: same score, new `date`, `change_basis: reaffirmed`, a rationale stating "no material change since <previous date>", and the sources actually checked during the review.

The research prompt explicitly instructs that reaffirmation is the default and that finding nothing new is an acceptable answer. The proportion of reaffirmed entries is reported each month, with no target; a high proportion is not an anomaly.

### 5.2 Admissible reasons for a change

A score may change only for one of the following reasons, declared in `change_basis` and explained in `change_reason`:

| `change_basis` | Meaning | Traceability required |
|---|---|---|
| `new_information` | A source published after the previous entry's date brings material information. | The new source is cited, with why it is material. |
| `previously_omitted` | Information published before the previous entry was missed, misread, or becomes interpretable only in light of a newer source. | The older source is cited and explicitly labeled `previously_omitted`, with why it was not incorporated before and why it is incorporated now. |
| `lookback_expiry` | Novelty only: a previously cited event leaves the 90-day lookback window without a new event replacing it. | The expired event and its date are cited. |

Every change needs at least one source of tier 1 to 3 (section 3), except `lookback_expiry`.

Rules that prevent silent backfill:

- a `previously_omitted` correction takes effect only from the new entry's `date`; the earlier entry, and any frozen snapshot that used it, are never edited;
- the share of `previously_omitted` changes is reported each month, per ticker; a ticker with repeated corrections is flagged for audit (section 9).

## 6. Validity, transition and missing data

1. An entry remains valid for 35 days after its `date` (existing rule of `docs/WEEKLY_SIGNALS.md`). The 4-week rotation keeps every ticker inside that window, with a 7-day margin.
2. **Baseline review at transition:** before the v2 activation snapshot, every one of the 33 tickers receives a `baseline` review under this protocol, which supersedes any earlier entry. No cross-section of a v2-eligible snapshot therefore mixes entries from the old and the new procedure. The rotation of section 4 starts with the following week.
3. After 35 days without a new or reaffirmed entry, the component is missing, the Signal Score is null and the observation is not v2-eligible. It is never imputed or carried forward beyond 35 days.
4. A missed review is reported as such. It is never backfilled later with a back-dated entry.
5. An entry is never edited after it has been used by a frozen snapshot. A correction is a new entry with a later date.

## 7. Required provenance fields

In addition to the existing `score`, `date`, `rationale` and `sources` fields:

| Field | Content |
|---|---|
| `research_protocol` | `research-v2.0` |
| `review_id` | unique identifier of the review |
| `review_type` | `baseline`, `scheduled` or `event:<type>` |
| `model` | model identifier actually used |
| `prompt_sha256` | SHA-256 of `config/research_prompt_v2.md` |
| `previous_date` | date of the previous entry for this component, or `null` |
| `previous_score` | score of the previous entry for this component, or `null` |
| `change_basis` | `baseline`, `reaffirmed`, `new_information`, `previously_omitted` or `lookback_expiry` |
| `change_reason` | free text, mandatory unless `change_basis` is `reaffirmed` |
| `source_tags` | for each source: tier 1-6, and `previously_omitted: true` when applicable |

A validator must reject a v2 entry missing any of these fields, a score change with `change_basis: reaffirmed`, and a `reaffirmed` entry whose score differs from `previous_score` (activation condition 4 of `PREREGISTRATION_V2.md`).

## 8. Scoring anchors

The anchors at 0, 25, 50, 75 and 100 for each component are defined in `config/research_prompt_v2.md`. They are fixed before the first baseline review. Existing v1 entries are not rescored retrospectively.

Expected consequence, declared in advance: v1 entries produced before the change were written without anchors, with 1 or 2 sources each, and with novelty scores between 65 and 95. Anchored scoring may shift the level of the qualitative components for the 10 v1 tickers. This is precisely why v1 amendment v1.4 requires a before/after sensitivity analysis.

## 9. Audit

1. Each month, a random sample of 10 % of the month's entries (at least 3) is checked by the project owner: sources exist, were published before the entry date, support the rationale, and `change_basis` is correct. Results are recorded in a dated audit log.
2. Every `previously_omitted` change is audited, in addition to the sample.
3. An entry that fails the audit is not edited. The failure is recorded, and the next review produces a new entry.
4. Exploratory option: an independent second scoring of a sample by a different model or person, to measure inter-rater agreement, reported separately and never used as a score input.

## Changelog

| Version | Date | Change |
|---|---|---|
| v2.0 (draft) | 2026-10-01 | Initial draft. |
| v2.0 (draft, rev. 2) | 2026-10-01 | Scope set to all 33 tickers; change rule widened to `previously_omitted` and `lookback_expiry` with traceability; baseline review at transition; anchors moved to the prompt file. |
