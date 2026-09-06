\set ON_ERROR_STOP on
BEGIN;
-- SPY dates are the P3-validated US session spine. Preserve gaps in other tickers.
CREATE OR REPLACE VIEW trading_prices AS
WITH sessions AS (
 SELECT price_date, row_number() OVER (ORDER BY price_date) AS session_no
 FROM prices WHERE ticker='SPY'
), grid AS (
 SELECT t.ticker,s.price_date,s.session_no,p.adjusted_close,p.volume
 FROM (SELECT DISTINCT ticker FROM prices) t CROSS JOIN sessions s
 LEFT JOIN prices p ON p.ticker=t.ticker AND p.price_date=s.price_date
)
SELECT *,
 lag(adjusted_close) OVER w AS previous_close,
 lag(price_date) OVER w AS previous_close_date,
 lead(adjusted_close,4) OVER w AS fifth_close,
 lead(price_date,4) OVER w AS fifth_session,
 count(adjusted_close) OVER (PARTITION BY ticker ORDER BY session_no ROWS BETWEEN CURRENT ROW AND 4 FOLLOWING) AS forward_count,
 avg(volume) OVER (PARTITION BY ticker ORDER BY session_no ROWS BETWEEN 60 PRECEDING AND 1 PRECEDING) AS prior_volume_avg,
 count(volume) OVER (PARTITION BY ticker ORDER BY session_no ROWS BETWEEN 60 PRECEDING AND 1 PRECEDING) AS prior_volume_count
FROM grid WINDOW w AS (PARTITION BY ticker ORDER BY session_no);

CREATE OR REPLACE VIEW event_metric_inputs AS
SELECT e.candidate_id,e.ticker,e.event_date,e.release_timing,e.event_type,e.analysis_scope,e.sample_role,
 r.price_date AS reaction_date,r.previous_close_date,r.fifth_session,
 r.previous_close,r.adjusted_close AS reaction_close,r.fifth_close,r.forward_count,
 r.volume AS reaction_volume,r.prior_volume_avg,r.prior_volume_count,
 CASE WHEN e.ticker='SOXX' THEN 'SPY' ELSE 'SOXX' END AS benchmark,
 b.previous_close AS benchmark_previous_close,b.adjusted_close AS benchmark_reaction_close,
 b.fifth_close AS benchmark_fifth_close,b.forward_count AS benchmark_forward_count,
 x.actual_eps,x.consensus_eps,(x.candidate_id IS NOT NULL) AS eps_eligible
FROM events e
LEFT JOIN LATERAL (
 SELECT * FROM trading_prices p WHERE p.ticker=e.ticker
 AND (p.price_date>e.event_date OR (p.price_date=e.event_date AND e.release_timing<>'amc'))
 ORDER BY p.session_no LIMIT 1
) r ON TRUE
LEFT JOIN trading_prices b ON b.ticker=CASE WHEN e.ticker='SOXX' THEN 'SPY' ELSE 'SOXX' END AND b.price_date=r.price_date
LEFT JOIN automatic_eps_inputs x ON x.candidate_id=e.candidate_id;

CREATE OR REPLACE VIEW event_metrics_live AS
WITH calculations AS (
 SELECT *,
 100*(actual_eps-consensus_eps)/nullif(abs(consensus_eps),0) AS eps_surprise_pct,
 actual_eps-consensus_eps AS eps_difference,
 100*(reaction_close/nullif(previous_close,0)-1) AS return_1d_pct,
 CASE WHEN forward_count=5 THEN 100*(fifth_close/nullif(previous_close,0)-1) END AS return_5d_pct,
 100*(benchmark_reaction_close/nullif(benchmark_previous_close,0)-1) AS benchmark_return_1d_pct,
 CASE WHEN benchmark_forward_count=5 THEN 100*(benchmark_fifth_close/nullif(benchmark_previous_close,0)-1) END AS benchmark_return_5d_pct,
 CASE WHEN prior_volume_count=60 THEN reaction_volume/nullif(prior_volume_avg,0) END AS volume_ratio_60d
 FROM event_metric_inputs
)
SELECT *,return_1d_pct-benchmark_return_1d_pct AS excess_return_1d_pp,
 return_5d_pct-benchmark_return_5d_pct AS excess_return_5d_pp,
 CASE WHEN NOT eps_eligible OR eps_difference IS NULL OR return_1d_pct IS NULL
        OR eps_difference=0 OR return_1d_pct=0 THEN NULL
      WHEN sign(eps_difference)<>sign(return_1d_pct) THEN 'divergent' ELSE 'aligned' END AS calculated_pattern
FROM calculations;

-- A persisted snapshot for later API reads; refresh explicitly after input changes.
CREATE MATERIALIZED VIEW IF NOT EXISTS event_metrics AS SELECT * FROM event_metrics_live WITH NO DATA;
REFRESH MATERIALIZED VIEW event_metrics;
CREATE UNIQUE INDEX IF NOT EXISTS event_metrics_candidate_idx ON event_metrics(candidate_id);
DO $$ BEGIN
 IF (SELECT count(*) FROM event_metrics)<>20 THEN RAISE EXCEPTION 'Expected 20 metric rows'; END IF;
 IF EXISTS (SELECT 1 FROM event_metrics WHERE return_1d_pct IS NULL OR return_5d_pct IS NULL
 OR prior_volume_count<>60 OR volume_ratio_60d IS NULL OR excess_return_1d_pp IS NULL OR excess_return_5d_pp IS NULL)
 THEN RAISE EXCEPTION 'Incomplete price/benchmark/volume coverage'; END IF;
 IF (SELECT count(*) FROM event_metrics WHERE eps_eligible)<>11 THEN RAISE EXCEPTION 'EPS eligibility changed'; END IF;
 IF EXISTS (SELECT 1 FROM event_metrics WHERE NOT eps_eligible AND (eps_surprise_pct IS NOT NULL OR calculated_pattern IS NOT NULL))
 THEN RAISE EXCEPTION 'Ineligible EPS calculation'; END IF;
END $$;
COMMIT;
