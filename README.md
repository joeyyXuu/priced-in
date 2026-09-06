# Priced In

**When a beat still sinks the stock.**

Priced In is a retrospective semiconductor event-study project that examines why a stock can fall after apparently strong earnings—and why it can rise after weak results. It connects reported performance and management guidance with the market's actual reaction.

The project is intentionally narrow: semiconductor-related events from 2019–2025, a small group of companies, and a manually reviewed dataset. It is not a prediction tool, a trading signal, or a real-time market-data product.

## Project status

P1 seed validation and the local PostgreSQL setup (P2) are complete. Historical price collection (P3) is complete for the approved event windows. P4 consensus-estimate acceptance is also complete; P5 SQL metrics are complete; the read-only FastAPI layer (P6) is implemented. The frontend now displays API data.

- `data/events_candidates.csv` preserves all 26 original records and research notes, plus new candidates C27 and C28. Original fields are archival and may contain superseded values.
- `data/events.csv` contains the curated 20-event sample: 13 earnings, four guidance, and three macro events across seven tickers and 2019–2025.
- `data/event_review.csv` records inclusion decisions and every existing-field correction, including normalized metadata for excluded candidates.
- `data/estimates.csv` contains 13 sourced actual/consensus EPS pairs: 11 have reviewed comparable bases; C19/C25 remain unverified and are retained for qualitative analysis only.
- C12 is anchored to the export rule's October 7 public-inspection filing at 11:15 AM Eastern and is classified `intraday`.
- `data/p1_validation.csv` documents eight beat/down sign-divergence cases and three aligned comparisons (C03, C11, C23), using published next-session closing observations. These are manually supported sample roles, not computed or causally established effects.

See [the P1 review](docs/P1_REVIEW.md) for findings, sources, corrections, and the TSM exclusion from automatic EPS analysis. The database holds the same approved sample, with 11 eligible EPS inputs and two blocked TSM pairs.

The frontend is served by FastAPI at http://127.0.0.1:8000/.

## Research question

The [frontend](web/events-draft.html) preserves the supplied design and fetches actual events and stored metrics from the API. Open http://127.0.0.1:8000/ after starting the service; opening the HTML directly from disk does not provide the API connection.

The project asks:

> When a semiconductor company beats expectations, why can its stock still fall?

An earnings headline is only one part of the event. The market may react more strongly to forward guidance, valuation, product delays, changes in demand, policy announcements, or expectations that were already reflected in the share price.

## Dataset

The candidate dataset covers:

- **Period:** 2019–2025
- **Tickers:** NVDA, AMD, INTC, TSM, MU, AVGO, and SOXX
- **Event types:** earnings, guidance, macro/policy, and product announcements
- **Patterns:** aligned reactions, potential divergences, and macro events
- **Sources:** company investor-relations pages, SEC filings, and government or reputable financial-news sources

The events are manually selected rather than randomly sampled. This is a purposive event sample covering every year from 2019 through 2025, with greater weight on the recent AI cycle. It is not a balanced panel. The approved annual counts are 2019: 1, 2020: 1, 2021: 1, 2022: 4, 2023: 4, 2024: 6, and 2025: 3. The candidate pool is designed to include potential expectation/reaction divergences, ordinary control cases, and macro events that affected the semiconductor sector without a company earnings release.

## Data dictionary

| Column | Description |
|---|---|
| `candidate_id` | Stable identifier used while reviewing the candidate pool. |
| `ticker` | Company ticker or `SOXX`, used as the semiconductor-sector proxy. |
| `approx_period` | Approximate month originally used to locate the event. |
| `event_date` | Actual announcement date in `YYYY-MM-DD` format. |
| `release_timing` | `bmo` = before market open, `amc` = after market close, `intraday` = during market hours. |
| `event_type` | Primary event category: `earnings`, `guidance`, `macro`, or `product`. |
| `fiscal_quarter` | Reported company quarter in `FYxxQx` format, such as `FY24Q1`; blank for macro and acquisition events. |
| `expected_pattern` | Pre-analysis hypothesis: `aligned`, `divergent`, or `macro`. It is not the calculated result. |
| `why_selected` | Short explanation of why the event belongs in the candidate pool. |
| `headline` | Short factual event description, separate from interpretation in `why_selected`. |
| `recall_confidence` | Initial confidence in the candidate description before full validation. |
| `source_url` | Source used to validate the event. |
| `verified` | Event metadata, date, and timing verification only; TRUE does not establish EPS comparability. |
| `release_time_et` | Documented announcement/publication time in America/New_York, `HH:MM`; blank when only the session category is established. |
| `timing_source_url`, `timing_notes` | Evidence and scope of the timing assertion; a syndication time is not necessarily the earliest publication. |
| `sample_role` | Selection role: `divergence_candidate`, `comparison`, `additional_aligned`, `qualitative`, or `macro`; never a computed flag. |
| `analysis_scope` | `eps_and_price` for comparable earnings, `macro_price` for macro events, or `qualitative` for guidance and unverified EPS cases. |

The production dictionary applies to `events.csv`. The research archive retains original wording and formatting; `event_review.csv` supplies its reviewed values. The review log's `field_corrections` captures old and new values; all production rows also gain headline, timing-evidence, and sample-role fields.

Fiscal years are company-specific, not calendar labels: NVIDIA's May 2023 release is `FY24Q1`, and TSMC's January 2025 release reports `FY24Q4`. For guidance events, this field identifies the quarter **reported**, not the future period guided. A later quantitative guidance dataset must store its own target period. Macro and acquisition events have no fiscal quarter.

### What “guidance” means

Guidance is management's forward-looking outlook, such as expected revenue, margins, EPS, or demand for a future quarter or year. It is different from both the results already reported and analysts' consensus estimates. An event is labelled `guidance` when the forward outlook is the main reason the event was selected.

## Reaction-day methodology

`event_date` is the announcement date, but it is not always the correct market-reaction date.

| Release timing | Reaction-day convention |
|---|---|
| `bmo` | First trading day on or after `event_date`. |
| `amc` | First trading day after `event_date`. |
| `intraday` | First trading day on or after `event_date`. The daily close-to-close window includes some pre-announcement trading. |

This distinction prevents an after-hours earnings release from being matched to a return that occurred before the information became public.

Use US trading sessions and available price dates to handle weekends and holidays. A release documented at the 16:00 closing minute is classified `amc` when corroborated by an after-close schedule. Timing is interpreted in America/New_York, including daylight saving time. One-day reaction uses the close immediately before the reaction day as its baseline; five-day reaction ends on the fifth trading day counting the reaction day as day one.

The planned SQL layer will use trading-day indices and a per-event `LATERAL JOIN` to locate the appropriate reaction date. A 60-trading-day volume baseline will exclude the event day to avoid look-ahead bias.

## Planned metrics

- EPS surprise percentage
- One-day and five-day price reaction
- One-day excess return relative to SOXX
- Event-day volume relative to the prior 60-trading-day average
- Divergence between the earnings surprise and share-price direction

EPS actuals and consensus estimates will use one consistent basis—preferably non-GAAP—because mixing GAAP and non-GAAP values can create misleading surprise percentages.

Automatic EPS/price divergence requires an `earnings` event with `analysis_scope=eps_and_price` and a joined, verified comparable EPS pair. Require matching accounting basis, currency, share units, and split basis. Macro, product, and acquisition events are excluded. Guidance events remain qualitative unless comparable quantitative guidance expectations are separately collected; they do not become EPS divergence merely because the same release contains earnings.

The eligibility gate in `scripts/validate_seed.py` requires both `analysis_scope=eps_and_price` and `comparability_verified=TRUE`, finite non-null actual and consensus EPS, matching EPS bases, and matching currency, share unit, and split basis. The estimates CSV declares currency/share unit/split basis once for the pair, applying to both values; side-specific values, when supplied, must agree. `comparability_verified` controls EPS-pair admission but does not override analysis scope or missing/incompatible inputs. Event metadata verification is independent. C19/C25 remain excluded from both automatic EPS surprise and divergence.

For comparable earnings, the planned sign test compares `actual_eps - consensus_eps` with the one-day stock return. Opposite nonzero signs indicate mechanical divergence; zero or unavailable inputs produce no divergence classification. EPS surprise percentage uses `100 * (actual - consensus) / abs(consensus)`; zero consensus gives NULL percentage. This handles loss estimates without reversing beat/miss direction. These calculations belong in SQL, not the CSV validator. C16 (about -1.21%, softer outlook) and C22 (about -1.10%, overlapping Apple modem-business transaction) are weak/confounded sign-divergence cases, not evidence of the same causal strength as every other case. Five-day and SOXX-relative results are separate metrics and must not be substituted to fill the eight-case target. Guidance and concurrent news can explain a mechanical mismatch without proving the earnings caused the move.

### EPS inputs

`estimates.csv` joins on `candidate_id` and `fiscal_quarter`. It stores actual and consensus EPS, separate basis labels, currency, share unit, split basis, consensus snapshot date/kind, actual/consensus/comparison sources, a basis-review source, a comparability verification flag, and research notes. `USD` values for TSM are per ADR, not TWD per ordinary share. Historical NVIDIA values retain the share units used at each announcement; do not mix them with later split-restated EPS.

`consensus_snapshot_date` is a documentary proxy: the publication date of a preview, or the release-day results report for C22. It is not an exact analyst-vendor extraction timestamp. `snapshot_kind` distinguishes these cases. Sources come from different providers and may use different estimate panels. C01's preview was subsequently updated; contemporaneous results reporting corroborates its consensus value. These are manually researched retrospective inputs, not an immutable point-in-time feed. TSM actuals use `tifrs`; consensus basis is explicitly `unverified` and `comparability_verified=FALSE`. The TSM replacement sources have blank snapshot dates with `snapshot_kind=unverified_snapshot`; earlier Zacks sources and dates remain in their notes. `data/tsm_research.csv` preserves provisional C19/C20/C25 inputs, separate `usd_per_adr` units for actual and consensus, and reaction-window caveats. C20’s candidate pattern is corrected to aligned but it remains excluded. See the TSM supplement in the P1 review.

C22’s reported-at-release 0.89 consensus is accepted with its snapshot limitation because the EPS bases are comparable; the available pre-release 0.90 would still leave actual EPS of 1.06 classified as a beat.

C12 and C13 use reaction-day close-to-close returns that include pre-announcement trading, not pure post-announcement windows. C26 represents broad trade-policy/market sentiment; semiconductors were exempt from this reciprocal-tariff order. For SOXX macro events, use SPY/QQQ as a broader benchmark or leave excess return NULL. Never benchmark SOXX against itself. The current P1 sample adds no benchmark tickers; benchmark data collection belongs to P3.

## Planned architecture

See the [architecture overview](docs/ARCHITECTURE_OVERVIEW.md) for how the Python scripts, SQL files, Docker database, and planned API connect.

```text
Manually reviewed CSV
        ↓
Adjusted price-data script
        ↓
PostgreSQL event and price tables
        ↓
SQL reaction-metric layer
        ↓
FastAPI
        ↓
Web interface
```

The planned metric layer will use:

- `ROW_NUMBER()` to index trading days rather than assuming calendar-day offsets.
- `LATERAL JOIN` to find the correct reaction date for each event.
- Window functions to calculate the pre-event volume baseline.
- Precomputed reaction records so the eventual API does not depend on live external requests.

## Using the current dataset

Run the offline, standard-library CSV validation:

```sh
python3 scripts/validate_seed.py
python3 -m unittest discover -s tests -v
```

A successful check confirms structure, cross-file consistency, qualitative-only restrictions, and evidence coverage for eight sign-divergence cases plus three aligned comparisons. It checks the manually reviewed evidence; it does not independently certify websites or calculate financial metrics. The two blocked TSM pairs are reported separately. No dependencies, credentials, or network access are needed.

`p1_validation.csv` is an audit artifact, not the production price/reaction table. Its percentages are source-reported observations at differing precision. P3/P5 will collect adjusted prices and compute SQL metrics, then reconcile any discrepancies. P1 completion covers seed selection, not completion of those later analytical phases.

## Database import contract

The [schema](db/01_schema.sql) preserves all 18 event fields, stores EPS provenance and separate actual/consensus units, and provides an empty `prices` table for P3. The [loader](db/02_load_seed.sql) validates exact CSV headers with `HEADER MATCH`, stages text values, and imports explicitly named columns in one transaction. Repeat imports update matching IDs; failed imports roll back. `automatic_eps_inputs` implements the eligibility gate in SQL without computing financial metrics. See [the P2 import contract](docs/P2_IMPORT_CONTRACT.md).

### Local PostgreSQL setup

Requires Python 3 and Docker with Compose, with Docker running. Run from the repository root:

```sh
python3 scripts/db.py setup  # validate CSVs, start PostgreSQL 16, import seeds
python3 scripts/db.py check  # verify database membership and eligibility
python3 scripts/db.py test   # P1 tests plus live database integration tests
python3 scripts/db.py load  # reload approved CSVs after validation
python3 scripts/db.py stop  # stop the container, retaining its data
```

Setup generates a private, ignored `.env` if absent; `.env.example` documents the settings. Connect at `127.0.0.1:5433`, database/user `priced_in`, using the password in `.env`. Set `POSTGRES_PORT` before setup if that port is occupied. The container binds only to localhost and keeps data in the `priced-in_postgres_data` Docker volume. Run `setup` again to restart and reload. Changing `.env` does not rotate the password of an initialized database.

The verified seed has 20 events, 13 estimates, and 11 automatic EPS inputs. C19/C25 remain qualitative; research CSVs are not imported as computed results. P3 now supplies 12,448 historical price rows across eight tickers. Integration tests exercise repeated imports, header/membership rejection, constraints, independent eligibility gates, and rollback after a late import failure; temporary test mutations roll back. Schema creation is repeatable, but future schema changes require explicit migrations. This is a local development setup; API access and deployment configuration belong to later phases.

## Limitations

- The event sample is small and manually curated, so it is subject to selection bias.
- The candidate pool intentionally overrepresents notable or potentially divergent reactions.
- `expected_pattern` is a research hypothesis, not a computed conclusion.
- Consensus estimates will represent a snapshot rather than the full analyst-estimate distribution.
- Daily prices cannot isolate an announcement made during market hours as precisely as intraday data.
- The project is retrospective and should not be used as investment advice.

## Roadmap

- [x] Create and source the candidate event dataset
- [x] Add release-timing and fiscal-quarter fields
- [x] Resolve C12 timing and prepare a curated 20-event sample
- [x] Complete P1 seed acceptance: verify eight sign-divergence cases and three aligned comparisons; restrict unresolved TSM EPS pairs to qualitative analysis
- [x] Create the PostgreSQL schema and seed-data import
- [x] Collect adjusted historical prices
- [x] Complete P4 consensus acceptance: 13 audited pairs, 11 eligible, two qualitative-only
- [ ] Optional TSM EPS extension: reconcile two consensus bases before enabling automatic EPS analysis
- [x] Calculate reaction and divergence metrics in SQL
- [x] Build the FastAPI endpoints
- [x] Connect the web interface to the validated data
- [ ] Add a full methodology page and deployment

## Responsible use

This repository is an educational event-study project. It describes historical market reactions and does not provide forecasts, personalized investment recommendations, or trading advice.

## P3 historical prices

Run the price pipeline in a dedicated virtual environment (the tested environment uses Python 3.9):

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-prices.txt
.venv/bin/python scripts/prices.py
```

The first run downloads prices; later runs reuse hash-checked snapshots in ignored `data/prices/`. Use `--refresh` to replace snapshots with a new download. PostgreSQL must already be running. The importer validates all sessions before loading and checks the database values afterward. It preserves the approved event and estimate CSVs.

See [P3 review](docs/P3_REVIEW.md), [event coverage](data/p3_coverage.csv), and [corporate-action/volume checks](data/p3_quality.json). This phase stores adjusted closes and provider volume; it does not compute production return or divergence metrics.

## P4 consensus acceptance

Run `python3 scripts/validate_estimates.py` with PostgreSQL running to audit every estimate field against the database and compare Python/SQL eligibility. See [P4 review](docs/P4_REVIEW.md) and [row-level findings](data/p4_estimate_review.csv). The accepted dataset has 11 comparable pairs and two explicitly blocked TSM pairs; P5 can proceed with the documented snapshot limitations.

## P5 SQL metrics

Run `python3 scripts/metrics.py` to calculate and refresh the PostgreSQL metric snapshot, then `python3 scripts/test_metrics.py` for SQL regression tests. See [the SQL walkthrough](docs/P5_REVIEW.md), [calculated metrics](data/p5_metrics.csv), and [P1 reconciliation](data/p5_reconciliation.csv). All 20 events have price metrics; 11 have eligible EPS metrics, yielding eight divergences and three aligned cases. Re-run after any input update; the materialized snapshot does not refresh automatically.

## P6 read-only API

Run `python3 scripts/setup_api.py` with the database and P5 metrics ready, then open [interactive API docs](http://127.0.0.1:8000/docs). The API serves events, filters, event details and price windows from PostgreSQL through a SELECT-only login. See [P6 setup and endpoint contract](docs/P6_API.md). The frontend is available at the same address, `/`.

## Connected frontend

Open http://127.0.0.1:8000/ after `python3 scripts/setup_api.py`. Filter by event type, ticker, year or calculated pattern; select a headline for event sources, metrics and price windows. All event rows come from the API. See [frontend notes](docs/FRONTEND_INTEGRATION.md).
