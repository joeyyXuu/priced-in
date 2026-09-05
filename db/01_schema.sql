-- Applied inside the loader transaction. Future schema changes need migrations;
-- IF NOT EXISTS supports repeats, not automatic upgrades of incompatible tables.
CREATE TABLE IF NOT EXISTS events (
    candidate_id text PRIMARY KEY CHECK (candidate_id ~ '^C[0-9]{2,}$'),
    ticker text NOT NULL CHECK (ticker IN ('NVDA','AMD','INTC','TSM','MU','AVGO','SOXX')),
    approx_period text NOT NULL CHECK (approx_period ~ '^[0-9]{4}-[0-9]{2}$'),
    event_date date NOT NULL CHECK (event_date BETWEEN DATE '2019-01-01' AND DATE '2025-12-31'),
    release_timing text NOT NULL CHECK (release_timing IN ('bmo','amc','intraday')),
    event_type text NOT NULL CHECK (event_type IN ('earnings','guidance','macro','product','acquisition')),
    fiscal_quarter text,
    expected_pattern text NOT NULL CHECK (expected_pattern IN ('aligned','divergent','macro')),
    why_selected text NOT NULL CHECK (length(btrim(why_selected)) > 0),
    recall_confidence text NOT NULL CHECK (recall_confidence IN ('low','medium','high')),
    source_url text NOT NULL CHECK (source_url ~ '^https://[^/]+/'),
    verified boolean NOT NULL CHECK (verified),
    headline text NOT NULL CHECK (length(btrim(headline)) BETWEEN 1 AND 120),
    release_time_et time,
    timing_source_url text NOT NULL CHECK (timing_source_url ~ '^https://[^/]+/'),
    timing_notes text NOT NULL CHECK (length(btrim(timing_notes)) > 0),
    sample_role text NOT NULL CHECK (sample_role IN ('divergence_candidate','comparison','additional_aligned','qualitative','macro')),
    analysis_scope text NOT NULL CHECK (analysis_scope IN ('eps_and_price','qualitative','macro_price')),
    UNIQUE (candidate_id, fiscal_quarter),
    CHECK (approx_period = to_char(event_date, 'YYYY-MM')),
    CHECK (CASE WHEN event_type IN ('macro','acquisition') THEN fiscal_quarter IS NULL
                ELSE fiscal_quarter IS NOT NULL AND fiscal_quarter ~ '^FY[0-9]{2}Q[1-4]$' END),
    CHECK (CASE WHEN event_type = 'macro' THEN sample_role = 'macro' AND expected_pattern = 'macro' AND analysis_scope = 'macro_price'
                ELSE sample_role <> 'macro' AND expected_pattern <> 'macro' AND analysis_scope <> 'macro_price' END),
    CHECK ((sample_role = 'qualitative') = (analysis_scope = 'qualitative')),
    CHECK (analysis_scope <> 'eps_and_price' OR event_type = 'earnings'),
    CHECK (event_type <> 'guidance' OR analysis_scope = 'qualitative'),
    CHECK (sample_role <> 'divergence_candidate' OR (expected_pattern = 'divergent' AND analysis_scope = 'eps_and_price')),
    CHECK (sample_role NOT IN ('comparison','additional_aligned') OR (expected_pattern = 'aligned' AND analysis_scope = 'eps_and_price')),
    CHECK (release_time_et IS NULL OR
           (release_timing = 'bmo' AND release_time_et < TIME '09:30') OR
           (release_timing = 'intraday' AND release_time_et >= TIME '09:30' AND release_time_et < TIME '16:00') OR
           (release_timing = 'amc' AND release_time_et >= TIME '16:00'))
);

CREATE TABLE IF NOT EXISTS estimates (
    candidate_id text PRIMARY KEY,
    fiscal_quarter text NOT NULL,
    actual_eps numeric CHECK (actual_eps::text NOT IN ('NaN','Infinity','-Infinity')),
    consensus_eps numeric CHECK (consensus_eps::text NOT IN ('NaN','Infinity','-Infinity')),
    actual_eps_basis text NOT NULL CHECK (actual_eps_basis IN ('gaap','non_gaap','ifrs','tifrs')),
    consensus_eps_basis text NOT NULL CHECK (consensus_eps_basis IN ('gaap','non_gaap','ifrs','tifrs','unverified')),
    actual_currency text NOT NULL CHECK (actual_currency IN ('USD','TWD')),
    consensus_currency text NOT NULL CHECK (consensus_currency IN ('USD','TWD')),
    actual_share_unit text NOT NULL CHECK (actual_share_unit IN ('adr','diluted_common_share')),
    consensus_share_unit text NOT NULL CHECK (consensus_share_unit IN ('adr','diluted_common_share')),
    actual_split_basis text NOT NULL CHECK (length(btrim(actual_split_basis)) > 0),
    consensus_split_basis text NOT NULL CHECK (length(btrim(consensus_split_basis)) > 0),
    consensus_snapshot_date date,
    snapshot_kind text NOT NULL CHECK (snapshot_kind IN ('pre_release_publication','reported_at_release','unverified_snapshot')),
    actual_source_url text NOT NULL CHECK (actual_source_url ~ '^https://[^/]+/'),
    consensus_source_url text NOT NULL CHECK (consensus_source_url ~ '^https://[^/]+/'),
    comparison_source_url text NOT NULL CHECK (comparison_source_url ~ '^https://[^/]+/'),
    comparability_verified boolean NOT NULL,
    notes text NOT NULL CHECK (length(btrim(notes)) > 0),
    basis_review_source_url text NOT NULL CHECK (basis_review_source_url ~ '^https://[^/]+/'),
    FOREIGN KEY (candidate_id, fiscal_quarter) REFERENCES events(candidate_id, fiscal_quarter),
    CHECK (CASE WHEN snapshot_kind = 'unverified_snapshot' THEN consensus_snapshot_date IS NULL AND NOT comparability_verified
                ELSE consensus_snapshot_date IS NOT NULL END),
    CHECK (NOT comparability_verified OR
           (actual_eps IS NOT NULL AND consensus_eps IS NOT NULL AND actual_eps_basis = consensus_eps_basis
            AND actual_currency = consensus_currency AND actual_share_unit = consensus_share_unit
            AND actual_split_basis = consensus_split_basis))
);

-- P3 will populate this table; no prices or reaction metrics are invented in P2.
CREATE TABLE IF NOT EXISTS prices (
    ticker text NOT NULL CHECK (ticker IN ('NVDA','AMD','INTC','TSM','MU','AVGO','SOXX','SPY','QQQ')),
    price_date date NOT NULL,
    adjusted_close numeric NOT NULL CHECK (adjusted_close > 0 AND adjusted_close::text NOT IN ('NaN','Infinity','-Infinity')),
    volume bigint NOT NULL CHECK (volume >= 0),
    source text NOT NULL CHECK (length(btrim(source)) > 0),
    fetched_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (ticker, price_date)
);

CREATE INDEX IF NOT EXISTS events_ticker_date_idx ON events(ticker, event_date);
CREATE INDEX IF NOT EXISTS events_type_date_idx ON events(event_type, event_date);
CREATE INDEX IF NOT EXISTS events_scope_idx ON events(analysis_scope);

CREATE OR REPLACE VIEW automatic_eps_inputs AS
SELECT e.candidate_id, e.ticker, e.event_date, e.release_timing, e.fiscal_quarter,
       x.actual_eps, x.consensus_eps, x.actual_eps_basis AS eps_basis,
       x.actual_currency AS currency, x.actual_share_unit AS share_unit,
       x.actual_split_basis AS split_basis
FROM events e JOIN estimates x USING (candidate_id, fiscal_quarter)
WHERE e.event_type = 'earnings' AND e.analysis_scope = 'eps_and_price'
  AND x.comparability_verified IS TRUE
  AND x.actual_eps IS NOT NULL AND x.consensus_eps IS NOT NULL
  AND x.actual_eps::text NOT IN ('NaN','Infinity','-Infinity')
  AND x.consensus_eps::text NOT IN ('NaN','Infinity','-Infinity')
  AND x.actual_eps_basis = x.consensus_eps_basis
  AND x.actual_currency = x.consensus_currency AND x.actual_currency = 'USD'
  AND x.actual_share_unit = x.consensus_share_unit
  AND x.actual_share_unit = CASE WHEN e.ticker = 'TSM' THEN 'adr' ELSE 'diluted_common_share' END
  AND x.actual_split_basis = x.consensus_split_basis AND x.actual_split_basis = 'as_reported_at_event';

COMMENT ON COLUMN events.verified IS 'Event metadata/date/timing only; never EPS comparability.';
COMMENT ON VIEW automatic_eps_inputs IS 'Eligibility gate only; no surprise or return metrics. Both scope and comparable EPS are required.';
COMMENT ON TABLE prices IS 'P3 adjusted historical prices; SOXX macro excess returns use SPY/QQQ or NULL, never SOXX itself.';
