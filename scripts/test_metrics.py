"""Live SQL regression tests; all fixture mutations roll back."""
import unittest
from db import psql


def query(sql):
    return psql('-qAt',input=sql,text=True,capture_output=True).stdout.strip()


class MetricTests(unittest.TestCase):
    def test_hand_calculated_fixture(self):
        result=query('''BEGIN;
UPDATE estimates SET actual_eps=3,consensus_eps=2 WHERE candidate_id='C03';
UPDATE prices SET volume=100 WHERE ticker='NVDA' AND price_date BETWEEN '2023-05-01' AND '2023-08-23';
UPDATE prices SET adjusted_close=100 WHERE ticker IN ('NVDA','SOXX') AND price_date='2023-08-23';
UPDATE prices SET adjusted_close=110,volume=200 WHERE ticker='NVDA' AND price_date='2023-08-24';
UPDATE prices SET adjusted_close=120 WHERE ticker='NVDA' AND price_date='2023-08-30';
UPDATE prices SET adjusted_close=105 WHERE ticker='SOXX' AND price_date='2023-08-24';
UPDATE prices SET adjusted_close=110 WHERE ticker='SOXX' AND price_date='2023-08-30';
SELECT eps_surprise_pct=50 AND return_1d_pct=10 AND return_5d_pct=20
 AND excess_return_1d_pp=5 AND excess_return_5d_pp=10 AND volume_ratio_60d=2
 AND calculated_pattern='aligned' FROM event_metrics_live WHERE candidate_id='C03';
ROLLBACK;''')
        self.assertEqual(result,'t')

    def test_zero_and_loss_consensus(self):
        result=query('''BEGIN;
UPDATE estimates SET consensus_eps=0 WHERE candidate_id='C18';
SELECT eps_surprise_pct IS NULL FROM event_metrics_live WHERE candidate_id='C18';
UPDATE estimates SET actual_eps=-1,consensus_eps=-2 WHERE candidate_id='C18';
SELECT eps_surprise_pct=50 AND calculated_pattern='divergent' FROM event_metrics_live WHERE candidate_id='C18';
UPDATE estimates SET actual_eps=consensus_eps WHERE candidate_id='C18';
SELECT calculated_pattern IS NULL FROM event_metrics_live WHERE candidate_id='C18';
ROLLBACK;''')
        self.assertEqual(result.splitlines(),['t','t','t'])

    def test_gap_does_not_shift_reaction(self):
        result=query('''BEGIN;
DELETE FROM prices WHERE ticker='NVDA' AND price_date='2023-08-24';
SELECT reaction_date=DATE '2023-08-24' AND return_1d_pct IS NULL
 AND return_5d_pct IS NULL AND calculated_pattern IS NULL
 FROM event_metrics_live WHERE candidate_id='C03';
ROLLBACK;''')
        self.assertEqual(result,'t')

    def test_snapshot_and_scope(self):
        self.assertEqual(query('''SELECT count(*)=20 AND count(eps_surprise_pct)=11
 AND count(calculated_pattern)=11 FROM event_metrics;'''),'t')
        self.assertEqual(query('''SELECT count(*)=0 FROM (
(SELECT * FROM event_metrics EXCEPT SELECT * FROM event_metrics_live)
UNION ALL (SELECT * FROM event_metrics_live EXCEPT SELECT * FROM event_metrics)) q;'''),'t')
        self.assertEqual(query("SELECT bool_and(benchmark='SPY' AND eps_surprise_pct IS NULL AND calculated_pattern IS NULL) FROM event_metrics WHERE ticker='SOXX';"),'t')


if __name__ == '__main__':
    unittest.main(verbosity=2)
