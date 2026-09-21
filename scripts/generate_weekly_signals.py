"""Freeze one prospective snapshot per ISO week. See docs/WEEKLY_SIGNALS.md."""
import csv
import hashlib
import json
import math
import os
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ('fundamental_strength', 'novelty', 'pricing_headroom',
              'valuation', 'execution_risk')
METHOD = 'weekly-v1.0'
BENCHMARK = {'NVDA':'QQQ','AVGO':'QQQ','QCOM':'QQQ','MU':'QQQ','GOOGL':'QQQ','AMZN':'QQQ','ADI':'QQQ','MDT':'SPY','ISRG':'SPY','GH':'SPY'}


def number(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def scale(value, ceiling):
    return round(max(0, min(100, value / ceiling * 100)), 2) if number(value) else None


def validate_history(history):
    if not isinstance(history, list):
        raise ValueError('History must be an array')
    previous = ''
    for snapshot in history:
        day = date.fromisoformat(snapshot['date']).isoformat()
        if day <= previous or snapshot['frozen'] is not True or not snapshot['method_version']:
            raise ValueError('Invalid frozen history or date order')
        previous = day
        for score in snapshot['scores'].values():
            for key in ('signal_score', *COMPONENTS):
                value = score[key]
                if value is not None and (not number(value) or not 0 <= value <= 100):
                    raise ValueError(f'Invalid {key}')
        top = snapshot['top3']
        if not isinstance(top, list) or len(top) > 3 or len(set(top)) != len(top):
            raise ValueError('Invalid top3')
        if any(t not in snapshot['scores'] or snapshot['scores'][t]['signal_score'] is None for t in top):
            raise ValueError('Top3 requires complete scores')


def research_score(entry, component, today):
    item = entry.get(component)
    if item is None:
        return None
    observed = date.fromisoformat(item['date'])
    if observed > today:
        raise ValueError('Research cannot be future-dated')
    if not number(item['score']) or not 0 <= item['score'] <= 100:
        raise ValueError('Research score must be between 0 and 100')
    if not isinstance(item.get('rationale'), str) or not item['rationale'].strip():
        raise ValueError('Research requires a rationale')
    sources = item.get('sources')
    if not isinstance(sources, list) or not sources or any(
        not isinstance(url, str) or not url.startswith(('https://', 'http://')) for url in sources
    ):
        raise ValueError('Research requires source URLs')
    return item['score'] if (today - observed).days <= 35 else None


def generate(root=ROOT, now=None):
    # The canonical repository history is reserved for the official scheduled
    # path. Tests may use an isolated root, but local/push/PR invocations may
    # not consume the production ISO week.
    if root.resolve() == ROOT.resolve() and os.getenv('GITHUB_EVENT_NAME') != 'schedule':
        raise RuntimeError('Canonical weekly snapshots may be frozen only by the schedule event')
    now = now or datetime.now(timezone.utc)
    today = now.astimezone(timezone.utc).date()
    target = root / 'data/weekly_signals.json'
    original = target.read_bytes()
    history = json.loads(original)
    validate_history(history)
    if history:
        last = date.fromisoformat(history[-1]['date'])
        if last > today:
            raise ValueError('Refusing to backdate a snapshot')
        if last.isocalendar()[:2] == today.isocalendar()[:2]:
            return False
    fundamentals_raw = (root / 'data/fundamentals.json').read_bytes()
    fundamentals = json.loads(fundamentals_raw)
    generated = datetime.fromisoformat(fundamentals['generated_at'].replace('Z', '+00:00'))
    if generated.tzinfo is None or not 0 <= (now - generated).total_seconds() <= 7 * 86400:
        raise ValueError('Fundamentals must have been collected within the past seven days')
    research_raw = (root / 'data/signal_research.json').read_bytes()
    research = json.loads(research_raw)
    with (root / 'data/universe_seed.csv').open() as stream:
        tickers = [row['ticker'] for row in csv.DictReader(stream)]
    if set(research) - set(tickers):
        raise ValueError('Unknown research ticker')
    scores = {}
    for ticker in tickers:
        company = fundamentals['companies'].get(ticker, {})
        latest = company.get('latest', {}) if company.get('status') == 'ok' else {}
        margin, roic = scale(latest.get('fcf_margin_pct'), 30), scale(latest.get('roic_pct'), 20)
        score = dict.fromkeys(COMPONENTS)
        score['fundamental_strength'] = round((margin + roic) / 2, 2) if margin is not None and roic is not None else None
        score['valuation'] = scale(latest.get('fcf_yield_pct'), 5)
        for component in ('novelty', 'pricing_headroom', 'execution_risk'):
            score[component] = research_score(research.get(ticker, {}), component, today)
        missing = [key for key in COMPONENTS if score[key] is None]
        score['signal_score'] = None if missing else round((
            score['fundamental_strength'] + score['novelty'] + score['pricing_headroom']
            + score['valuation'] + 100 - score['execution_risk']) / 5, 2)
        score['missing_components'] = missing
        score['inputs'] = {'fundamentals': latest, 'research': research.get(ticker, {})}
        scores[ticker] = score
    ranked = sorted((t for t in tickers if scores[t]['signal_score'] is not None),
                    key=lambda t: (-scores[t]['signal_score'], t))
    t0_after_session = {}
    boundary_path = root / 'data/market_boundary_runtime.json'
    if os.getenv('REQUIRE_MARKET_BOUNDARY') == '1':
        if not boundary_path.exists():
            raise ValueError('Confirmatory snapshot requires current market boundary')
        boundary = json.loads(boundary_path.read_text())
        observed = datetime.fromisoformat(boundary['observed_at'].replace('Z', '+00:00'))
        if observed > now or (now-observed).total_seconds() > 3600:
            raise ValueError('Market boundary must come from the current scheduled run')
        latest = boundary['latest_returned_session']
        market_universe = set(BENCHMARK) | set(BENCHMARK.values())
        missing_market = sorted(market_universe - set(latest))
        if missing_market:
            raise ValueError(f'Missing market boundary series: {missing_market}')
        # market.py computes this span on the union of sessions returned in the
        # same vendor response, so weekends/holidays do not masquerade as drift.
        if boundary.get('alignment_span_sessions') not in (0, 1):
            raise ValueError('Confirmatory market boundaries are not aligned within one session')
        global_boundary = boundary.get('global_boundary')
        if global_boundary != max(latest[t] for t in market_universe):
            raise ValueError('Invalid global market boundary')
        for ticker in BENCHMARK:
            t0_after_session[ticker] = global_boundary
    snapshot = {'date': today.isoformat(), 'frozen': True, 'method_version': METHOD,
                'captured_at': now.isoformat(), 'scores': scores, 'top3': ranked[:3],
                'fundamentals_generated_at': fundamentals['generated_at'],
                't0_after_session': t0_after_session,
                'input_sha256': {name: hashlib.sha256(raw).hexdigest() for name, raw in
                                 [('fundamentals', fundamentals_raw), ('research', research_raw)]}}
    validate_history(history + [snapshot])
    # Preserve every existing snapshot byte; insert only before the closing bracket.
    end = original.rstrip()
    if not end.endswith(b']'):
        raise ValueError('Invalid history terminator')
    addition = json.dumps(snapshot, ensure_ascii=False, indent=2, allow_nan=False).encode()
    updated = end[:-1] + (b',\n' if history else b'\n') + addition + b'\n]\n'
    temporary = target.with_suffix('.json.tmp')
    temporary.write_bytes(updated)
    os.replace(temporary, target)
    return True


if __name__ == '__main__':
    print('Weekly snapshot appended' if generate() else 'This week is already frozen; no changes')
