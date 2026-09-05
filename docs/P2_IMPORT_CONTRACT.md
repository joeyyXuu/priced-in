# P2 seed import contract

P1 membership is human-approved. P2 is implemented in [the schema](../db/01_schema.sql), [transactional loader](../db/02_load_seed.sql), and [database acceptance checks](../db/03_verify_seed.sql). Run `python3 scripts/db.py setup` from the repository root; see the [README](../README.md#local-postgresql-setup) for connection and lifecycle commands. The approved CSV files are unchanged.

## Events: exact staging order

Load `data/events.csv` into a dedicated staging table with all 18 text columns in this exact order. Specify the column list explicitly in the COPY command; `HEADER` alone does not map CSV names to table columns.

| Position | Staging and destination column | Destination type |
|---|---|---|
| 1 | candidate_id | text, unique/not null |
| 2 | ticker | text |
| 3 | approx_period | text |
| 4 | event_date | date |
| 5 | release_timing | text |
| 6 | event_type | text |
| 7 | fiscal_quarter | nullable text |
| 8 | expected_pattern | text |
| 9 | why_selected | text |
| 10 | recall_confidence | text |
| 11 | source_url | text |
| 12 | verified | boolean |
| 13 | headline | text |
| 14 | release_time_et | nullable time |
| 15 | timing_source_url | text |
| 16 | timing_notes | text |
| 17 | sample_role | text |
| 18 | analysis_scope | text |

The loader must validate the exact source header, stage the rows, then explicitly INSERT into the named destination columns above, selecting each staging column by name. Convert `event_date` to date and `verified` to boolean; convert empty fiscal-quarter and release-time strings to NULL, casting the latter to time. Validate allowed enums, unique IDs, required fields, the 20 approved IDs, and role/year counts within the transaction before promoting rows. Fail atomically on errors. Do not use `INSERT ... SELECT *` or a positional `\copy events FROM events.csv` against a seven-column table. If P2 chooses a narrower core table, an explicit projection and a keyed metadata table must preserve the remaining fields, particularly eligibility and provenance.

## Estimates and automatic analysis

Use a separate explicitly mapped staging import for `estimates.csv`. Join estimates to events by `candidate_id` and matching `fiscal_quarter`. Empty snapshot dates are NULL; `unverified_snapshot` records remain blocked. Convert EPS to numeric and comparability to boolean without converting missing values to zero.

Every future automatic EPS-surprise/divergence query must require all of:

- `events.event_type = 'earnings'` and `events.analysis_scope = 'eps_and_price'`.
- `estimates.comparability_verified IS TRUE`.
- Actual and consensus EPS are non-null finite numbers.
- Actual and consensus accounting bases are equal and recognized, including `tifrs`.
- Actual and consensus currency, share unit, and split basis match.

The current estimates CSV has one currency/share-unit/split-basis tuple applying to both EPS values. Preserve that contract at import; never normalize only one side. If the database separates those fields per side, populate both from the pair tuple and enforce equality before analysis. `events.verified` only describes event metadata and must not substitute for EPS comparability. C19/C25 remain qualitative and unverified for automatic EPS, despite their provisional numbers. Regression coverage lives in `tests/test_p1_validation.py`; P2/P5 must reproduce the gate in SQL before exposing metrics.

Do not seed production computed metrics from `p1_validation.csv` or `tsm_research.csv`. These are research evidence, not SQL outputs. Preserve the candidate archive separately; only `events.csv` defines production membership.

## Reaction and benchmark constraints

Map `bmo` and `intraday` to the first available trading session on or after the announcement, and `amc` strictly after it. Intraday close-to-close windows include pre-announcement trading. For SOXX macro events use a broader SPY/QQQ benchmark if collected, or NULL excess return. Never calculate a SOXX-against-SOXX excess return. The choice of broader benchmark and price ingestion will be implemented in their later phases.

## P2 implementation and validation

PostgreSQL 16 receives all 18 event columns and all 17 estimate CSV columns through temporary text staging tables. Both COPY commands use explicit column lists and `HEADER MATCH`. The pair-level CSV currency, share unit, and split basis each populate separate actual/consensus database columns; all provenance and notes are retained. Nullable dates, quarters, and times remain NULL. Numeric EPS is never filled with zero.

The loader serializes imports with a transaction advisory lock, validates staging membership, role/year counts, coverage, snapshots and units, then applies named upserts under database constraints. Post-import checks run before COMMIT. Any failure rolls back the whole transaction, including prior event updates. Extra production rows are rejected rather than silently deleted. Re-running the same import leaves seed contents unchanged; incompatible existing schemas require a migration.

`automatic_eps_inputs` is the shared SQL admission view for future metrics. It yields the 11 approved comparable earnings inputs; C19/C25 remain excluded. The `prices` table is ready for P3 and initially empty. No reaction, surprise, or divergence metric is computed during P2.

`python3 scripts/db.py test` runs the existing 10 P1 regression tests and seven live database tests in `scripts/test_database.py`. Database tests cover PostgreSQL version, idempotent reloads, header order, approved membership, late-failure rollback, field/foreign-key/comparability constraints, and independent scope/comparability gates. They verify that event and estimate contents are unchanged afterward. Run against this local development database with no concurrent writers.
