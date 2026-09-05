"""Regression checks for the human-approved sample and automatic EPS gate."""

import unittest
from collections import Counter
from datetime import date
from decimal import Decimal

from scripts.validate_seed import (
    APPROVED_ROLES, APPROVED_YEARS, automatic_eps_eligible, load_csv, main,
)


class P1ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = {r['candidate_id']: r for r in load_csv('events.csv', {'candidate_id'})}
        cls.estimates = {r['candidate_id']: r for r in load_csv('estimates.csv', {'candidate_id'})}

    def test_existing_checks(self):
        main()

    def test_approved_membership_counts_and_years(self):
        expected = {'C01', 'C02', 'C03', 'C04', 'C06', 'C07', 'C09', 'C10', 'C11', 'C12',
                    'C13', 'C16', 'C18', 'C19', 'C22', 'C23', 'C25', 'C26', 'C27', 'C28'}
        self.assertEqual(set(self.events), expected)
        self.assertEqual(Counter(r['sample_role'] for r in self.events.values()), APPROVED_ROLES)
        self.assertEqual(Counter(date.fromisoformat(r['event_date']).year
                                 for r in self.events.values()), APPROVED_YEARS)

    def test_exact_automatic_subset(self):
        eligible = {cid for cid, event in self.events.items()
                    if automatic_eps_eligible(event, self.estimates.get(cid, {}))}
        self.assertEqual(eligible, {'C01', 'C03', 'C04', 'C09', 'C11', 'C16', 'C18',
                                    'C22', 'C23', 'C27', 'C28'})

    def test_tsm_excluded_even_with_numeric_values_and_verified_metadata(self):
        for cid in ('C19', 'C25'):
            with self.subTest(cid=cid):
                event, estimate = self.events[cid], self.estimates[cid]
                self.assertEqual(event['verified'], 'TRUE')
                self.assertTrue(Decimal(estimate['actual_eps']).is_finite())
                self.assertTrue(Decimal(estimate['consensus_eps']).is_finite())
                self.assertFalse(automatic_eps_eligible(event, estimate))
                # Changing scope alone must not override unresolved comparability.
                self.assertFalse(automatic_eps_eligible(dict(event, analysis_scope='eps_and_price'), estimate))
                # Even a hypothetically comparable pair cannot override qualitative scope.
                comparable = dict(estimate, comparability_verified='TRUE', consensus_eps_basis='tifrs')
                self.assertFalse(automatic_eps_eligible(event, comparable))

    def test_both_gate_conditions_required(self):
        event, estimate = self.events['C01'], self.estimates['C01']
        self.assertTrue(automatic_eps_eligible(event, estimate))
        self.assertFalse(automatic_eps_eligible(dict(event, analysis_scope='qualitative'), estimate))
        self.assertFalse(automatic_eps_eligible(event, dict(estimate, comparability_verified='FALSE')))
        for event_type in ('guidance', 'macro', 'acquisition', 'product'):
            self.assertFalse(automatic_eps_eligible(dict(event, event_type=event_type), estimate))

    def test_missing_or_nonfinite_eps_rejected(self):
        for field in ('actual_eps', 'consensus_eps'):
            for value in (None, '', 'NaN', 'Infinity', 'not-a-number'):
                with self.subTest(field=field, value=value):
                    estimate = dict(self.estimates['C01'], **{field: value})
                    self.assertFalse(automatic_eps_eligible(self.events['C01'], estimate))

    def test_incompatible_basis_and_units_rejected(self):
        changes = {'consensus_eps_basis': 'gaap', 'currency': 'TWD', 'share_unit': 'adr',
                   'split_basis': 'restated', 'consensus_currency': 'TWD',
                   'actual_share_unit': 'adr', 'consensus_split_basis': 'restated'}
        for field, value in changes.items():
            with self.subTest(field=field):
                estimate = dict(self.estimates['C01'], **{field: value})
                self.assertFalse(automatic_eps_eligible(self.events['C01'], estimate))

    def test_wrong_join_rejected(self):
        self.assertFalse(automatic_eps_eligible(self.events['C01'], self.estimates['C03']))
        estimate = dict(self.estimates['C01'], fiscal_quarter='FY20Q3')
        self.assertFalse(automatic_eps_eligible(self.events['C01'], estimate))

    def test_c22_snapshot_limitation_does_not_change_beat(self):
        estimate = self.estimates['C22']
        self.assertEqual(estimate['snapshot_kind'], 'reported_at_release')
        self.assertEqual(estimate['consensus_eps'], '0.89')
        self.assertTrue(automatic_eps_eligible(self.events['C22'], estimate))
        for consensus in ('0.89', '0.90'):
            self.assertGreater(Decimal(estimate['actual_eps']), Decimal(consensus))

    def test_c12_sources(self):
        self.assertEqual(self.events['C12']['timing_source_url'],
                         'https://www.federalregister.gov/public-inspection/2022/10/07')
        self.assertEqual(self.events['C12']['source_url'],
                         'https://www.govinfo.gov/content/pkg/FR-2022-10-13/pdf/2022-21658.pdf')


if __name__ == '__main__':
    unittest.main()
