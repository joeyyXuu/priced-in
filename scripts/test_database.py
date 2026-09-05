"""Integration checks against the local P2 database; test mutations roll back."""

import subprocess
import unittest

from db import ROOT, psql


def query(sql):
    return psql('-qAt', input=sql, text=True, capture_output=True).stdout.strip()


def fingerprint():
    return query("""
        SELECT md5(jsonb_agg(to_jsonb(e) ORDER BY candidate_id)::text) FROM events e;
        SELECT md5(jsonb_agg(to_jsonb(x) ORDER BY candidate_id)::text) FROM estimates x;
    """)


class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        psql('-f', '/sql/03_verify_seed.sql', capture_output=True, text=True)
        cls.baseline = fingerprint()
        cls.loader = (ROOT / 'db/02_load_seed.sql').read_text().replace(
            r'\ir 01_schema.sql', r'\ir /sql/01_schema.sql').replace(
            r'\ir 03_verify_seed.sql', r'\ir /sql/03_verify_seed.sql')

    def tearDown(self):
        self.assertEqual(fingerprint(), self.baseline)

    def expect_failure(self, sql, message):
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            query(sql)
        self.assertIn(message, caught.exception.stderr)

    def staged_failure(self, mutation, message):
        sql = self.loader.replace('-- Validate the approved sample',
                                  mutation + '\n-- Validate the approved sample', 1)
        self.expect_failure(sql, message)

    def test_postgres_version(self):
        self.assertEqual(int(query('SHOW server_version_num;')) // 10000, 16)

    def test_repeated_import(self):
        for _ in range(2):
            psql('-f', '/sql/02_load_seed.sql', capture_output=True, text=True)
            self.assertEqual(fingerprint(), self.baseline)

    def test_header_order(self):
        self.expect_failure(self.loader.replace(
            r'\copy stage_events (candidate_id, ticker,',
            r'\copy stage_events (ticker, candidate_id,', 1),
            'column name mismatch')

    def test_membership_rejected(self):
        self.staged_failure("DELETE FROM stage_events WHERE candidate_id='C01';",
                            'Unapproved production membership')

    def test_late_failure_rolls_back_event_updates(self):
        self.staged_failure("""
            UPDATE stage_events SET headline='Rollback test' WHERE candidate_id='C01';
            UPDATE stage_estimates SET actual_eps_basis='unknown' WHERE candidate_id='C01';
        """, 'violates check constraint')

    def test_constraints(self):
        cases = [
            ("UPDATE events SET release_timing='unknown' WHERE candidate_id='C01'", 'check constraint'),
            ("UPDATE estimates SET fiscal_quarter='FY20Q1' WHERE candidate_id='C01'", 'foreign key constraint'),
            ("UPDATE estimates SET actual_eps_basis='gaap' WHERE candidate_id='C01'", 'check constraint'),
            ("UPDATE estimates SET actual_eps=NULL WHERE candidate_id='C01'", 'check constraint'),
            ("UPDATE estimates SET actual_eps='NaN' WHERE candidate_id='C01'", 'check constraint'),
            ("UPDATE estimates SET consensus_currency='TWD' WHERE candidate_id='C01'", 'check constraint'),
            ("UPDATE estimates SET consensus_share_unit='adr' WHERE candidate_id='C01'", 'check constraint'),
            ("UPDATE estimates SET consensus_split_basis='restated' WHERE candidate_id='C01'", 'check constraint'),
        ]
        for statement, message in cases:
            with self.subTest(statement=statement):
                self.expect_failure('BEGIN; ' + statement + '; ROLLBACK;', message)

    def test_scope_and_comparability_are_independent(self):
        result = query("""
            BEGIN;
            UPDATE events SET analysis_scope='eps_and_price', sample_role='comparison'
                WHERE candidate_id IN ('C19','C25');
            SELECT count(*) FROM automatic_eps_inputs WHERE candidate_id IN ('C19','C25');
            ROLLBACK;
            BEGIN;
            UPDATE estimates SET consensus_eps_basis='tifrs', comparability_verified=TRUE,
                snapshot_kind='reported_at_release',
                consensus_snapshot_date=(SELECT event_date FROM events e WHERE e.candidate_id=estimates.candidate_id)
                WHERE candidate_id IN ('C19','C25');
            SELECT count(*) FROM automatic_eps_inputs WHERE candidate_id IN ('C19','C25');
            ROLLBACK;
            BEGIN;
            UPDATE estimates SET comparability_verified=FALSE WHERE candidate_id='C01';
            SELECT count(*) FROM automatic_eps_inputs WHERE candidate_id='C01';
            ROLLBACK;
        """)
        self.assertEqual(result.splitlines(), ['0', '0', '0'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
