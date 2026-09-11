# Research Engine V2

## Goal

Turn the market dashboard into a prospective research system for AI/semi, robotics and biotech/medtech.

The core question is not "which stock belongs to a hot theme?" but:

> Where is demand accelerating, what bottleneck does it create, which listed supplier becomes difficult to substitute, and are financials confirming the change before valuation fully reflects it?

## Six independent lenses

Never collapse the research into one magic recommendation score. Display separately:

1. Industrial signal
2. Financial confirmation
3. Criticality / substitutability
4. Exposure materiality
5. Valuation temperature
6. Evidence diversity

## Evidence discipline

Preferred hierarchy:

1. Regulatory filings and official results
2. Customer / supplier primary confirmation
3. Earnings calls and investor presentations
4. Reputable independent reporting
5. Estimates
6. Hypotheses

A hypothesis may generate a research task but never a verified relationship.

## Relationship graph

Every important relationship should be stored as an edge:

`anchor -> supplier -> tier-2 supplier`

with date, evidence, value-chain node, criticality, materiality and estimated replacement/qualification time.

The most interesting pattern is a supplier moving from one anchor to several independent anchors while orders, backlog or margins accelerate.

## Research cards

Each company card should eventually expose:

- theme and role
- value-chain node
- linked anchors
- what changed recently
- primary evidence
- industrial signal
- financial confirmation
- criticality and substitution time
- valuation temperature
- catalyst
- explicit falsification condition
- price at detection
- M1/M3/M6/M12 outcome vs benchmark

## Dashboard target views

### Radar
Rank recent changes by velocity, materiality and evidence diversity.

### Blockbusters / Anchors
Show where capital, orders, clinical demand and product launches originate.

### Critical Enablers
Show bottlenecks and picks-and-shovels, especially multi-anchor suppliers.

### Emerging / Future Gems
Small and mid caps only when a concrete observable event can promote them from watchlist to candidate.

### Devil's Advocate
Surface concentration, substitution, dilution, regulation, clinical failure, margin pressure and valuation risk.

### Prospective Validation
Never rewrite the original thesis. Add M1/M3/M6/M12 returns later and compare with QQQ; use XBI as a secondary benchmark for biotech when relevant.

## Next vertical slice

1. SEC/EDGAR company filings and fundamentals
2. Primary-source evidence ingestion
3. Deterministic event extraction
4. Relationship graph population
5. Static dashboard sections for anchors/enablers/catalysts/falsification
