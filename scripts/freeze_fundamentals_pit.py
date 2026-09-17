#!/usr/bin/env python3
"""Append immutable fundamental observations from the current collector output.

The ledger freezes what the project actually observed. It does not claim that
Yahoo statements are an institutional filing-time point-in-time feed.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/fundamentals.json'
OUT_DIR = ROOT / 'data/fundamentals_pit'
UNIVERSE = ROOT / 'data/universe_seed.csv'
SCHEMA_VERSION = 'fundamentals-pit-v1'


def parse_dt(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('generated_at must include timezone')
    return dt


def build_observations(payload):
    observed = parse_dt(payload['generated_at']).astimezone(timezone.utc)
    with UNIVERSE.open(encoding='utf-8') as stream:
        allowed = {row['ticker'] for row in csv.DictReader(stream)}
    rows = []
    for ticker in sorted(allowed):
        company = payload.get('companies', {}).get(ticker, {})
        if company.get('status') != 'ok':
            continue
        latest = company.get('latest', {})
        rows.append({
            'schema_version': SCHEMA_VERSION,
            'observation_id': f"FUND-{observed.strftime('%Y%m%dT%H%M%SZ')}-{ticker}",
            'ticker': ticker,
            'observed_at': observed.isoformat().replace('+00:00', 'Z'),
            'source': 'yfinance-standardized-statements',
            'source_generated_at': payload['generated_at'],
            'fiscal_year': latest.get('year'),
            'metrics': {k: latest.get(k) for k in (
                'revenue','ocf','capex','fcf','capex_ocf_pct','fcf_margin_pct',
                'fcf_per_share','roic_pct','fcf_yield_pct',
                'fcf_cagr_available_pct','fcf_per_share_cagr_available_pct'
            )},
            'frozen': True,
        })
    return rows


def append_only(existing, new_rows):
    if not isinstance(existing, list):
        raise ValueError('fundamentals PIT journal must be an array')
    ids = {x['observation_id'] for x in existing}
    additions = [x for x in new_rows if x['observation_id'] not in ids]
    return existing + additions, len(additions)


def main():
    payload = json.loads(SOURCE.read_text(encoding='utf-8'))
    rows = build_observations(payload)
    month = parse_dt(payload['generated_at']).strftime('%Y-%m')
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUT_DIR / f'{month}.json'
    existing = json.loads(target.read_text(encoding='utf-8')) if target.exists() else []
    updated, added = append_only(existing, rows)
    target.write_text(json.dumps(updated, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(f'{target}: appended {added} observation(s)')


if __name__ == '__main__':
    main()
