"""P4 parity checks reject silent changes to values, units and provenance."""
import csv
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from validate_estimates import compare_pair


class EstimateAuditTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        with (root / 'data/estimates.csv').open() as f:
            self.seed = next(csv.DictReader(f))
        self.stored = dict(self.seed)
        for field in ('currency', 'share_unit', 'split_basis'):
            value = self.stored.pop(field)
            for side in ('actual_', 'consensus_'):
                self.stored[side + field] = value
        self.stored['comparability_verified'] = True

    def test_equivalent_numeric_representation(self):
        self.stored['actual_eps'] = '1.2300'
        compare_pair(self.seed, self.stored)

    def test_drift_rejected(self):
        for field, value in [('consensus_eps', '1.12'), ('consensus_share_unit', 'adr'),
                             ('notes', 'lost provenance'), ('consensus_snapshot_date', None),
                             ('comparability_verified', False)]:
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, field):
                compare_pair(self.seed, {**self.stored, field:value})


if __name__ == '__main__':
    unittest.main()
