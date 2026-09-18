import importlib.util
import unittest
from pathlib import Path

P = Path(__file__).parent / 'freeze_fundamentals_pit.py'
spec = importlib.util.spec_from_file_location('fundpit', P)
fundpit = importlib.util.module_from_spec(spec); spec.loader.exec_module(fundpit)


class FundamentalPITTests(unittest.TestCase):
    def test_append_preserves_existing_observation(self):
        old = [{'observation_id':'FUND-A','ticker':'NVDA','metrics':{'fcf':10},'frozen':True}]
        revised_same_id = [{'observation_id':'FUND-A','ticker':'NVDA','metrics':{'fcf':99},'frozen':True}]
        result, added = fundpit.append_only(old, revised_same_id)
        self.assertEqual(added, 0)
        self.assertEqual(result[0]['metrics']['fcf'], 10)

    def test_new_observation_is_appended(self):
        old = [{'observation_id':'FUND-A','ticker':'NVDA','metrics':{},'frozen':True}]
        new = [{'observation_id':'FUND-B','ticker':'NVDA','metrics':{'fcf':20},'frozen':True}]
        result, added = fundpit.append_only(old, new)
        self.assertEqual(added, 1)
        self.assertEqual([x['observation_id'] for x in result], ['FUND-A','FUND-B'])


if __name__ == '__main__':
    unittest.main()
