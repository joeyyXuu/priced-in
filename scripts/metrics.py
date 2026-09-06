"""Run P5 SQL and export calculated results; Python performs no financial math."""
import sys
from db import ROOT, psql, run


def main():
    run([sys.executable, '-B', str(ROOT / 'scripts/validate_estimates.py')])
    psql('-f', '/sql/04_metrics.sql')
    result = psql('--csv', '-c', 'SELECT * FROM event_metrics ORDER BY candidate_id', capture_output=True, text=True)
    (ROOT / 'data/p5_metrics.csv').write_text(result.stdout)
    # Research values are staged only for comparison, never used as metric inputs.
    sql = r'''
BEGIN;
CREATE TEMP TABLE evidence (candidate_id text,reaction_date date,"window" text,eps_result text,price_direction text,reviewed_pattern text,reported_return_pct numeric,evidence_kind text,source_url text,corroborating_source_url text,reviewed_on date,verified boolean,notes text);
\copy evidence FROM '/seed/p1_validation.csv' WITH (FORMAT csv, HEADER MATCH)
COPY (
 SELECT m.candidate_id,m.reaction_date,e.reaction_date AS evidence_reaction_date,
 m.eps_surprise_pct,m.return_1d_pct,e.reported_return_pct,
 m.return_1d_pct-e.reported_return_pct AS difference_pp,
 m.calculated_pattern,e.reviewed_pattern,
 CASE WHEN m.reaction_date<>e.reaction_date OR m.calculated_pattern IS DISTINCT FROM e.reviewed_pattern
 OR abs(m.return_1d_pct-e.reported_return_pct)>0.10 THEN 'REVIEW' ELSE 'CONSISTENT_WITHIN_0.10_PP' END AS reconciliation,
 e.notes
 FROM event_metrics m JOIN evidence e USING(candidate_id) ORDER BY m.candidate_id
) TO STDOUT WITH (FORMAT csv, HEADER);
ROLLBACK;
'''
    result = psql('-q', input=sql, capture_output=True, text=True)
    (ROOT / 'data/p5_reconciliation.csv').write_text(result.stdout)
    print('Exported data/p5_metrics.csv and data/p5_reconciliation.csv')


if __name__ == '__main__':
    main()
