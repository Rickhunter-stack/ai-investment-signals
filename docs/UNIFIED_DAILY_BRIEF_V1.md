# Unified Daily Brief v1

## Purpose

Use one daily research pass instead of three overlapping products: general daily brief, AI-sector review and AMD/competitor review. The same evidence base produces a short human brief with exactly five high-value signals and prospective structured events for AI Investment Signals.

This is a research workflow, not a recommendation engine.

## Unit of selection: signal/story, not article

The daily Top 5 contains five distinct events or evolving stories. Several articles about the same industrial development are consolidated into one item and strengthen evidence diversity rather than consume several Top-5 slots.

Prioritize material new facts, leading adoption signals, bottleneck/criticality changes, competitive changes, financial or valuation dislocations, and falsification or contradiction of an existing thesis.

General medicine, health, tech or travel may enter the human Top 5 when important. Only investment-relevant items enter the investment journal.

## Human output

Each item should compactly distinguish FACT, WEAK_SIGNAL and optional HYPOTHESIS, then state the story/thesis impact, value-chain node, leading adoption evidence when applicable, companies/assets to watch when evidenced, pricing check, and the next observable that would strengthen or weaken the thesis.

Keep the readable brief to roughly 3-4 minutes.

## Persistent company and sector research

AMD, Nvidia, Broadcom, TSMC, Micron and other recurring companies are persistent research subjects, not mandatory daily sections. A company appears in the Top 5 only when new evidence materially changes its story, adoption state, competitive position, fundamentals, valuation temperature or falsification risk.

Likewise, AI-sector analysis is persistent context. Daily events update the relevant value-chain story rather than recreate a complete sector report.

## Leading Adoption Signals

For emerging technologies, describe the most advanced independently evidenced stage when useful:

0. Hype / demonstration
1. Technical validation
2. Real customer pilot
3. Pilot expansion / repeat deployment
4. Supply-chain commitment / capacity / qualification
5. Commercial commitment / firm order
6. Revenue acceleration

This stage is descriptive evidence, not a score or recommendation. Do not promote a stage without dated evidence.

## Separate signal strength from investment attractiveness

Never collapse the research into one magic score. Strong adoption does not imply valuation headroom; a falling share price does not imply undervaluation; a strong company does not imply an attractive entry point; and a hot theme does not establish a supplier relationship.

Keep the Research Engine V2 lenses separate: industrial signal, financial confirmation, criticality/substitutability, exposure materiality, valuation temperature and evidence diversity.

A useful research pattern is improving leading evidence while valuation expectations remain modest, but this must be tested prospectively rather than asserted from hindsight.

## Investment-journal output

After the human brief, only investment-relevant items are eligible for `brief-event-v1` ingestion. Follow `DAILY_BRIEF_INGESTION.md`, `STORY_DEDUP_V1.md` and the schema.

Reliable timezone-aware `published_at` is mandatory prospectively. Compare against all frozen history before choosing story relation, reuse permanent story IDs, write to immutable daily journals, never backfill or rewrite frozen events, and never invent tickers, dates, sources, scores or relationships.

Do not modify `weekly_signals.json`, `signal_research.json` or weekly scores from the daily brief. Quantitative confirmation and weekly scoring remain separate downstream processes.

## Daily pipeline

```text
Fresh sources
 -> candidate facts
 -> cluster by story
 -> compare with frozen history
 -> update persistent theses/companies
 -> rank by novelty + materiality + leading value + evidence quality
 -> exactly 5 human-readable signals
 -> investment-relevance gate
 -> brief-event-v1 daily journal
 -> downstream weekly research / prospective validation
```

## Success criterion

Detect when the future starts becoming observable before it becomes obvious in reported financials, while preserving enough timestamped evidence to test later whether those early signals actually had predictive value.
