"""Collector runtime dependencies that otherwise fail only on specific vendor data."""
import ast
import importlib
import unittest
from pathlib import Path

from src import market

ROOT = Path(__file__).resolve().parents[1]


class MarketCollectorDependencyTests(unittest.TestCase):
    def test_price_repair_dependency_is_installed(self):
        # yfinance reconstructs anomalous bars with sklearn only when it detects one,
        # so a missing extra surfaces as a per-ticker failure on an arbitrary night.
        if market.REQUEST.get("repair"):
            importlib.import_module("sklearn.cluster")

    def test_downloads_are_single_threaded(self):
        tree = ast.parse((ROOT / "src/market.py").read_text(encoding="utf-8"))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == "download"]
        self.assertTrue(calls)
        for call in calls:
            threads = [k.value for k in call.keywords if k.arg == "threads"]
            self.assertEqual(len(threads), 1, "yf.download must pass threads explicitly")
            self.assertIs(threads[0].value, False)


if __name__ == "__main__":
    unittest.main()
