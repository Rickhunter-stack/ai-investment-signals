import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from generate_weekly_signals import generate, validate_history


class WeeklySignalsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'data').mkdir()
        self.write('weekly_signals', [])
        self.write('signal_research', {})
        (self.root / 'data/universe_seed.csv').write_text('ticker\nAAA\nBBB\n')
        self.fundamentals()

    def write(self, name, value):
        (self.root / f'data/{name}.json').write_text(json.dumps(value))

    def fundamentals(self, day=14):
        self.write('fundamentals', {'generated_at': f'2026-09-{day}T10:00:00Z', 'companies': {
            'AAA': {'status': 'ok', 'latest': {'fcf_margin_pct': 30, 'roic_pct': 20, 'fcf_yield_pct': 5}},
            'BBB': {'status': 'ok', 'latest': {'fcf_margin_pct': 3, 'roic_pct': 2, 'fcf_yield_pct': 0.5}}}})

    def run_at(self, day):
        return generate(self.root, datetime(2026, 9, day, 21, tzinfo=timezone.utc))

    def history(self):
        return json.loads((self.root / 'data/weekly_signals.json').read_text())

    def test_confirmatory_snapshot_freezes_t0_boundary(self):
        self.write('signal_research', {})
        boundary={'observed_at':'2026-09-14T20:50:00+00:00','latest_returned_session':{'AAA':'2026-09-14','BBB':'2026-09-14'}}
        (self.root/'data/market_boundary_runtime.json').write_text(json.dumps(boundary))
        import generate_weekly_signals as g
        with patch.dict(g.BENCHMARK,{'AAA':'BBB','BBB':'AAA'},clear=True), patch.dict(os.environ,{'REQUIRE_MARKET_BOUNDARY':'1'}):
            self.assertTrue(self.run_at(14))
        self.assertEqual(self.history()[0]['t0_after_session']['AAA'],'2026-09-14')

    def test_partial_and_ticker_specific(self):
        self.assertTrue(self.run_at(14))
        snap = self.history()[0]
        self.assertEqual(snap['scores']['AAA']['fundamental_strength'], 100)
        self.assertEqual(snap['scores']['BBB']['fundamental_strength'], 10)
        self.assertIsNone(snap['scores']['AAA']['signal_score'])
        self.assertEqual(snap['top3'], [])

    def test_idempotent_and_append_preserves_bytes(self):
        self.run_at(14)
        path = self.root / 'data/weekly_signals.json'
        original = path.read_bytes()
        self.assertFalse(self.run_at(18))
        self.assertEqual(path.read_bytes(), original)
        self.fundamentals(21)
        self.assertTrue(self.run_at(21))
        self.assertTrue(path.read_bytes().startswith(original.rstrip()[:-1]))
        self.assertEqual(self.history()[0], json.loads(original)[0])

    def test_complete_score_and_risk_direction(self):
        self.write('signal_research', {'AAA': {k: {'score': v, 'date': '2026-09-14',
                   'rationale': 'Test fixture only', 'sources': ['https://example.com/filing']}
                   for k, v in [('novelty', 80), ('pricing_headroom', 60), ('execution_risk', 100)]}})
        self.run_at(14)
        snap = self.history()[0]
        self.assertEqual(snap['scores']['AAA']['signal_score'], 68)
        self.assertEqual(snap['top3'], ['AAA'])

    def test_stale_fundamentals_fail_without_write(self):
        with self.assertRaises(ValueError):
            self.run_at(22)
        self.assertEqual(self.history(), [])

    def test_invalid_research_fails_without_write(self):
        for score in [True, float('nan'), 101]:
            self.write('signal_research', {'AAA': {'novelty': {'score': score, 'date': '2026-09-14'}}})
            with self.assertRaises(ValueError):
                self.run_at(14)
            self.assertEqual(self.history(), [])

    def test_stale_research_is_missing(self):
        self.write('signal_research', {'AAA': {'novelty': {'score': 80, 'date': '2026-07-01',
                   'rationale': 'Old analysis', 'sources': ['https://example.com/filing']}}})
        self.run_at(14)
        self.assertIsNone(self.history()[0]['scores']['AAA']['novelty'])

    def test_future_history_rejected(self):
        self.fundamentals(21)
        self.run_at(21)
        with self.assertRaises(ValueError):
            self.run_at(14)

    def test_unfrozen_history_rejected(self):
        self.run_at(14)
        history = self.history()
        history[0]['frozen'] = False
        with self.assertRaises(ValueError):
            validate_history(history)


if __name__ == '__main__':
    unittest.main()
