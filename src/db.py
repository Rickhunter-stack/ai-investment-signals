from pathlib import Path
import sqlite3

DB_PATH = Path('data/veille.db')

SCHEMA = '''
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS companies (
    ticker TEXT PRIMARY KEY,
    company TEXT NOT NULL,
    theme TEXT NOT NULL,
    role TEXT NOT NULL,
    subtheme TEXT,
    priority INTEGER DEFAULT 2,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS market (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    close REAL,
    volume REAL,
    market_cap REAL,
    PRIMARY KEY (ticker, date)
);
-- Prospective point-in-time market ledger. Rows are immutable after first insert.
-- adjusted_close is used consistently for securities and benchmarks so future
-- performance includes split/dividend adjustments on the same basis.
CREATE TABLE IF NOT EXISTS market_pit (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    adjusted_close REAL NOT NULL,
    volume REAL,
    observed_at TEXT NOT NULL,
    source TEXT NOT NULL,
    series_type TEXT NOT NULL CHECK(series_type IN ('security','benchmark')),
    PRIMARY KEY (ticker, date)
);
CREATE TABLE IF NOT EXISTS signals (
    signal_id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    family TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    value REAL,
    source_url TEXT,
    event_id TEXT,
    rules_version TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scores (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    family TEXT NOT NULL,
    score REAL NOT NULL,
    rules_version TEXT NOT NULL,
    breakdown_json TEXT,
    PRIMARY KEY (ticker, date, family, rules_version)
);
CREATE TABLE IF NOT EXISTS watchlist (
    ticker TEXT PRIMARY KEY,
    status TEXT,
    target_review_date TEXT,
    note TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    step TEXT NOT NULL,
    sources_ok TEXT,
    sources_failed TEXT,
    rules_version TEXT,
    log_path TEXT
);
'''

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    return conn
