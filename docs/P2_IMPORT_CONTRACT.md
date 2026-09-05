# P2 seed import contract

P1 membership is human-approved. No PostgreSQL schema or loader currently exists. This contract specifies the required staging approach for P2, not an implemented database service.

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
