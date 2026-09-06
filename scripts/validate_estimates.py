"""P4 read-only CSV/database parity audit; no financial metric calculations."""
import csv
from decimal import Decimal
import json
from db import ROOT, psql, validate
from validate_seed import automatic_eps_eligible


def compare_pair(seed, stored):
    expanded = dict(seed)
    for field in ('currency', 'share_unit', 'split_basis'):
        value = expanded.pop(field)
        expanded['actual_' + field] = value
        expanded['consensus_' + field] = value
    for field, expected in expanded.items():
        actual = stored[field]
        if field in ('actual_eps', 'consensus_eps'):
            equal = actual is not None and Decimal(str(actual)) == Decimal(expected)
        elif field == 'comparability_verified':
            equal = actual is (expected == 'TRUE')
        else:
            equal = actual == (expected or None)
        if not equal:
            raise ValueError(f"{seed['candidate_id']}: database mismatch in {field}")


def main():
    validate()
    seeds = list(csv.DictReader((ROOT / 'data/estimates.csv').open()))
    events = {r['candidate_id']:r for r in csv.DictReader((ROOT / 'data/events.csv').open())}
    # One read-only transaction gives a consistent view of estimates and eligibility.
    sql = '''BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SELECT json_build_object('estimates',(SELECT json_agg(x) FROM estimates x),
 'eligible',(SELECT json_agg(candidate_id ORDER BY candidate_id) FROM automatic_eps_inputs));
COMMIT;'''
    state = json.loads(psql('-qAt', input=sql, text=True, capture_output=True).stdout)
    stored = {r['candidate_id']:r for r in state['estimates']}
    if set(stored) != {r['candidate_id'] for r in seeds}:
        raise ValueError('Estimate membership mismatch')
    eligible = sorted(r['candidate_id'] for r in seeds if automatic_eps_eligible(events[r['candidate_id']], r))
    if eligible != state['eligible']:
        raise ValueError('Python/SQL EPS eligibility mismatch')
    report = []
    for r in seeds:
        compare_pair(r, stored[r['candidate_id']])
        report.append(dict(candidate_id=r['candidate_id'], fiscal_quarter=r['fiscal_quarter'],
            actual_eps=r['actual_eps'], consensus_eps=r['consensus_eps'],
            snapshot_kind=r['snapshot_kind'], consensus_snapshot_date=r['consensus_snapshot_date'],
            disposition='accepted_retrospective' if r['candidate_id'] in eligible else 'qualitative_only',
            database_parity='PASS',
            limitation='Consensus basis and replacement snapshot unverified' if r['candidate_id'] not in eligible
            else 'Updated preview; release-day corroboration retained' if r['candidate_id']=='C01'
            else 'Release-day consensus 0.89; pre-release preview 0.90' if r['candidate_id']=='C22'
            else 'Publication date proxy; no immutable vendor snapshot'))
    with (ROOT / 'data/p4_estimate_review.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(report[0]))
        writer.writeheader()
        writer.writerows(report)
    print(f'P4 PASS: {len(seeds)} complete field mappings; {len(eligible)} eligible; 2 qualitative-only. No database writes.')


if __name__ == '__main__':
    main()
