\set ON_ERROR_STOP on
BEGIN;
SELECT pg_advisory_xact_lock(731902);
SET LOCAL datestyle = 'ISO, YMD';
\ir 01_schema.sql
LOCK TABLE events, estimates IN SHARE ROW EXCLUSIVE MODE;
CREATE TEMP TABLE stage_events (
    candidate_id text,
    ticker text,
    approx_period text,
    event_date text,
    release_timing text,
    event_type text,
    fiscal_quarter text,
    expected_pattern text,
    why_selected text,
    recall_confidence text,
    source_url text,
    verified text,
    headline text,
    release_time_et text,
    timing_source_url text,
    timing_notes text,
    sample_role text,
    analysis_scope text) ON COMMIT DROP;
\copy stage_events (candidate_id, ticker, approx_period, event_date, release_timing, event_type, fiscal_quarter, expected_pattern, why_selected, recall_confidence, source_url, verified, headline, release_time_et, timing_source_url, timing_notes, sample_role, analysis_scope) FROM '/seed/events.csv' WITH (FORMAT csv, HEADER MATCH)
CREATE TEMP TABLE stage_estimates (
    candidate_id text,
    fiscal_quarter text,
    actual_eps text,
    consensus_eps text,
    actual_eps_basis text,
    consensus_eps_basis text,
    currency text,
    share_unit text,
    split_basis text,
    consensus_snapshot_date text,
    snapshot_kind text,
    actual_source_url text,
    consensus_source_url text,
    comparison_source_url text,
    comparability_verified text,
    notes text,
    basis_review_source_url text) ON COMMIT DROP;
\copy stage_estimates (candidate_id, fiscal_quarter, actual_eps, consensus_eps, actual_eps_basis, consensus_eps_basis, currency, share_unit, split_basis, consensus_snapshot_date, snapshot_kind, actual_source_url, consensus_source_url, comparison_source_url, comparability_verified, notes, basis_review_source_url) FROM '/seed/estimates.csv' WITH (FORMAT csv, HEADER MATCH)

-- Validate the approved sample before any row promotion. HEADER MATCH checks names/order.
DO $$ BEGIN
IF (SELECT count(*) FROM stage_events) <> 20 OR (SELECT count(DISTINCT candidate_id) FROM stage_events) <> 20 OR EXISTS (SELECT 1 FROM stage_events WHERE candidate_id IS NULL OR candidate_id NOT IN ('C01', 'C02', 'C03', 'C04', 'C06', 'C07', 'C09', 'C10', 'C11', 'C12', 'C13', 'C16', 'C18', 'C19', 'C22', 'C23', 'C25', 'C26', 'C27', 'C28')) THEN RAISE EXCEPTION 'Unapproved production membership'; END IF;
IF (SELECT jsonb_object_agg(sample_role, n) FROM (SELECT sample_role, count(*) n FROM stage_events GROUP BY sample_role) q)
    IS DISTINCT FROM '{"divergence_candidate":8,"comparison":3,"macro":3,"qualitative":6}'::jsonb
THEN RAISE EXCEPTION 'Incorrect role distribution'; END IF;
IF (SELECT jsonb_object_agg(y, n) FROM (SELECT extract(year FROM event_date::date)::int y, count(*) n FROM stage_events GROUP BY 1) q)
    IS DISTINCT FROM '{"2019":1,"2020":1,"2021":1,"2022":4,"2023":4,"2024":6,"2025":3}'::jsonb
THEN RAISE EXCEPTION 'Incorrect annual distribution'; END IF;
IF EXISTS (SELECT 1 FROM stage_events WHERE verified IS DISTINCT FROM 'TRUE')
   OR EXISTS (SELECT 1 FROM stage_estimates WHERE comparability_verified IS NULL OR comparability_verified NOT IN ('TRUE','FALSE'))
THEN RAISE EXCEPTION 'Invalid seed boolean'; END IF;
IF (SELECT count(*) FROM stage_estimates) <> 13 OR (SELECT count(DISTINCT candidate_id) FROM stage_estimates) <> 13
   OR EXISTS (SELECT 1 FROM stage_estimates x LEFT JOIN stage_events e USING (candidate_id)
              WHERE e.candidate_id IS NULL OR e.event_type <> 'earnings' OR x.fiscal_quarter IS DISTINCT FROM e.fiscal_quarter
                 OR x.actual_eps IS NULL OR x.consensus_eps IS NULL)
THEN RAISE EXCEPTION 'Incorrect earnings input coverage'; END IF;
IF EXISTS (SELECT 1 FROM stage_estimates x JOIN stage_events e USING (candidate_id)
           WHERE x.consensus_snapshot_date::date > e.event_date::date
              OR (x.snapshot_kind = 'reported_at_release' AND x.consensus_snapshot_date::date IS DISTINCT FROM e.event_date::date)
              OR x.currency IS DISTINCT FROM 'USD'
              OR x.share_unit IS DISTINCT FROM CASE WHEN e.ticker='TSM' THEN 'adr' ELSE 'diluted_common_share' END
              OR x.split_basis IS DISTINCT FROM 'as_reported_at_event')
THEN RAISE EXCEPTION 'Invalid estimate snapshot or units'; END IF;
END $$;
INSERT INTO events (candidate_id, ticker, approx_period, event_date, release_timing, event_type, fiscal_quarter, expected_pattern, why_selected, recall_confidence, source_url, verified, headline, release_time_et, timing_source_url, timing_notes, sample_role, analysis_scope)
SELECT candidate_id, ticker, approx_period, event_date::date, release_timing, event_type, NULLIF(fiscal_quarter, ''), expected_pattern, why_selected, recall_confidence, source_url, verified::boolean, headline, NULLIF(release_time_et, '')::time, timing_source_url, timing_notes, sample_role, analysis_scope
FROM stage_events
ON CONFLICT (candidate_id) DO UPDATE SET
    ticker = EXCLUDED.ticker,
    approx_period = EXCLUDED.approx_period,
    event_date = EXCLUDED.event_date,
    release_timing = EXCLUDED.release_timing,
    event_type = EXCLUDED.event_type,
    fiscal_quarter = EXCLUDED.fiscal_quarter,
    expected_pattern = EXCLUDED.expected_pattern,
    why_selected = EXCLUDED.why_selected,
    recall_confidence = EXCLUDED.recall_confidence,
    source_url = EXCLUDED.source_url,
    verified = EXCLUDED.verified,
    headline = EXCLUDED.headline,
    release_time_et = EXCLUDED.release_time_et,
    timing_source_url = EXCLUDED.timing_source_url,
    timing_notes = EXCLUDED.timing_notes,
    sample_role = EXCLUDED.sample_role,
    analysis_scope = EXCLUDED.analysis_scope;
INSERT INTO estimates (candidate_id, fiscal_quarter, actual_eps, consensus_eps, actual_eps_basis, consensus_eps_basis, actual_currency, consensus_currency, actual_share_unit, consensus_share_unit, actual_split_basis, consensus_split_basis, consensus_snapshot_date, snapshot_kind, actual_source_url, consensus_source_url, comparison_source_url, comparability_verified, notes, basis_review_source_url)
SELECT candidate_id, fiscal_quarter, actual_eps::numeric, consensus_eps::numeric, actual_eps_basis, consensus_eps_basis, currency, currency, share_unit, share_unit, split_basis, split_basis, NULLIF(consensus_snapshot_date, '')::date, snapshot_kind, actual_source_url, consensus_source_url, comparison_source_url, comparability_verified::boolean, notes, basis_review_source_url
FROM stage_estimates
ON CONFLICT (candidate_id) DO UPDATE SET
    fiscal_quarter = EXCLUDED.fiscal_quarter,
    actual_eps = EXCLUDED.actual_eps,
    consensus_eps = EXCLUDED.consensus_eps,
    actual_eps_basis = EXCLUDED.actual_eps_basis,
    consensus_eps_basis = EXCLUDED.consensus_eps_basis,
    actual_currency = EXCLUDED.actual_currency,
    consensus_currency = EXCLUDED.consensus_currency,
    actual_share_unit = EXCLUDED.actual_share_unit,
    consensus_share_unit = EXCLUDED.consensus_share_unit,
    actual_split_basis = EXCLUDED.actual_split_basis,
    consensus_split_basis = EXCLUDED.consensus_split_basis,
    consensus_snapshot_date = EXCLUDED.consensus_snapshot_date,
    snapshot_kind = EXCLUDED.snapshot_kind,
    actual_source_url = EXCLUDED.actual_source_url,
    consensus_source_url = EXCLUDED.consensus_source_url,
    comparison_source_url = EXCLUDED.comparison_source_url,
    comparability_verified = EXCLUDED.comparability_verified,
    notes = EXCLUDED.notes,
    basis_review_source_url = EXCLUDED.basis_review_source_url;
\ir 03_verify_seed.sql
COMMIT;
