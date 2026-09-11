"""Research-layer schema for the prospective investment radar.

Keeps facts, relationships, theses, narrative brief snapshots and market
outcomes separate so that historical signals are never rewritten after the fact.
"""

RESEARCH_SCHEMA = r'''
CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TEXT NOT NULL,
    published_at TEXT,
    source_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT,
    ticker TEXT,
    theme TEXT,
    excerpt TEXT NOT NULL,
    evidence_status TEXT NOT NULL CHECK(evidence_status IN ('verified','management','estimate','hypothesis','unverified')),
    content_hash TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date TEXT NOT NULL,
    ticker TEXT NOT NULL,
    theme TEXT NOT NULL,
    event_type TEXT NOT NULL,
    metric TEXT,
    old_value REAL,
    new_value REAL,
    unit TEXT,
    materiality REAL DEFAULT 0,
    evidence_id INTEGER,
    frozen_at TEXT NOT NULL,
    FOREIGN KEY(evidence_id) REFERENCES evidence(id)
);

CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observed_at TEXT NOT NULL,
    source_ticker TEXT NOT NULL,
    target_ticker TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    value_chain_node TEXT,
    criticality REAL DEFAULT 0,
    substitutability_years REAL,
    exposure_materiality REAL DEFAULT 0,
    evidence_id INTEGER,
    status TEXT NOT NULL DEFAULT 'unverified',
    FOREIGN KEY(evidence_id) REFERENCES evidence(id)
);

CREATE TABLE IF NOT EXISTS fundamentals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    period_end TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL,
    unit TEXT,
    source TEXT,
    UNIQUE(ticker, period_end, metric)
);

CREATE TABLE IF NOT EXISTS theses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    created_at TEXT NOT NULL,
    theme TEXT NOT NULL,
    role TEXT NOT NULL,
    thesis TEXT NOT NULL,
    catalyst TEXT,
    falsification TEXT NOT NULL,
    industrial_score REAL DEFAULT 0,
    financial_score REAL DEFAULT 0,
    criticality_score REAL DEFAULT 0,
    valuation_score REAL DEFAULT 0,
    evidence_diversity_score REAL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'watch',
    frozen INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS brief_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_date TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    summary TEXT NOT NULL,
    stance TEXT,
    themes TEXT,
    tickers TEXT,
    watch_next TEXT,
    invalidation TEXT,
    source_ref TEXT,
    frozen INTEGER NOT NULL DEFAULT 1,
    UNIQUE(brief_date, summary)
);

CREATE TABLE IF NOT EXISTS signal_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thesis_id INTEGER NOT NULL,
    horizon TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    price_return REAL,
    benchmark_return REAL,
    excess_return REAL,
    FOREIGN KEY(thesis_id) REFERENCES theses(id),
    UNIQUE(thesis_id, horizon)
);
'''


def ensure_research_schema(conn):
    conn.executescript(RESEARCH_SCHEMA)
    conn.commit()
