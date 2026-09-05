\set ON_ERROR_STOP on
DO $$ BEGIN
IF (SELECT count(*) FROM events) <> 20 OR EXISTS (SELECT 1 FROM events WHERE candidate_id NOT IN ('C01', 'C02', 'C03', 'C04', 'C06', 'C07', 'C09', 'C10', 'C11', 'C12', 'C13', 'C16', 'C18', 'C19', 'C22', 'C23', 'C25', 'C26', 'C27', 'C28')) THEN RAISE EXCEPTION 'Database membership differs from approved sample'; END IF;
IF (SELECT count(*) FROM estimates) <> 13 THEN RAISE EXCEPTION 'Expected 13 estimates'; END IF;
IF (SELECT jsonb_object_agg(sample_role,n) FROM (SELECT sample_role,count(*) n FROM events GROUP BY sample_role) q)
 IS DISTINCT FROM '{"divergence_candidate":8,"comparison":3,"macro":3,"qualitative":6}'::jsonb THEN RAISE EXCEPTION 'Database role mismatch'; END IF;
IF (SELECT jsonb_object_agg(y,n) FROM (SELECT extract(year FROM event_date)::int y,count(*) n FROM events GROUP BY 1) q)
 IS DISTINCT FROM '{"2019":1,"2020":1,"2021":1,"2022":4,"2023":4,"2024":6,"2025":3}'::jsonb THEN RAISE EXCEPTION 'Database year mismatch'; END IF;
IF (SELECT count(*) FROM automatic_eps_inputs) <> 11 OR EXISTS (SELECT 1 FROM automatic_eps_inputs WHERE candidate_id NOT IN ('C01', 'C03', 'C04', 'C09', 'C11', 'C16', 'C18', 'C22', 'C23', 'C27', 'C28')) THEN RAISE EXCEPTION 'Automatic EPS subset mismatch'; END IF;
IF EXISTS (SELECT 1 FROM events e JOIN estimates x USING (candidate_id,fiscal_quarter)
           WHERE e.candidate_id IN ('C19','C25') AND (e.analysis_scope <> 'qualitative' OR e.sample_role <> 'qualitative'
             OR x.actual_eps_basis <> 'tifrs' OR x.consensus_eps_basis <> 'unverified' OR x.comparability_verified))
THEN RAISE EXCEPTION 'TSM guard violated'; END IF;
IF NOT EXISTS (SELECT 1 FROM estimates WHERE candidate_id='C22' AND consensus_eps=0.89 AND snapshot_kind='reported_at_release')
THEN RAISE EXCEPTION 'C22 provenance changed'; END IF;
END $$;
SELECT 'events' AS relation, count(*) AS rows FROM events
UNION ALL SELECT 'estimates', count(*) FROM estimates
UNION ALL SELECT 'automatic_eps_inputs', count(*) FROM automatic_eps_inputs
UNION ALL SELECT 'prices', count(*) FROM prices;
