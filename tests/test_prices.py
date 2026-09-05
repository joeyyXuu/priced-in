"""Offline regression checks for P3 coverage and input rejection."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prices import event_windows, validate_rows


class PriceTests(unittest.TestCase):
    def test_timing_and_benchmark(self):
        from datetime import date, timedelta
        sessions = [(date(2024, 1, 1) + timedelta(days=i)).isoformat() for i in range(100)]
        events = [dict(candidate_id='C01', ticker='NVDA', event_date=sessions[70], release_timing=t)
                  for t in ['bmo', 'intraday', 'amc']]
        windows = event_windows(events, sessions)
        self.assertEqual([w['reaction_date'] for w in windows], [sessions[70], sessions[70], sessions[71]])
        self.assertEqual(windows[0]['fifth_session'], sessions[74])
        self.assertEqual(len(windows[0]['required']), 65)
        events[0]['ticker'] = 'SOXX'
        self.assertEqual(event_windows(events, sessions)[0]['benchmark'], 'SPY')

    def test_missing_session_not_skipped(self):
        with self.assertRaisesRegex(ValueError, 'Missing'):
            validate_rows([], {('NVDA', '2024-06-10')})

    def test_invalid_values_and_duplicates(self):
        row = dict(ticker='NVDA', price_date='2024-06-10', adjusted_close='120', volume='1000')
        validate_rows([row], {('NVDA', '2024-06-10')})
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            validate_rows([row, row], set())
        for field, value in [('adjusted_close', 'NaN'), ('adjusted_close', '0'),
                             ('volume', '-1'), ('volume', '0'), ('volume', '1.5')]:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                validate_rows([{**row, field:value}], set())


if __name__ == '__main__':
    unittest.main()
