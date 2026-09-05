# Priced In

**When a beat still sinks the stock.**

Priced In is a retrospective semiconductor event-study project that examines why a stock can fall after apparently strong earnings—and why it can rise after weak results. It connects reported performance and management guidance with the market's actual reaction.

The project is intentionally narrow: semiconductor-related events from 2019–2025, a small group of companies, and a manually reviewed dataset. It is not a prediction tool, a trading signal, or a real-time market-data product.

## Project status

P1 seed validation is complete for the defined sample. PostgreSQL (P2) is the next implementation phase.

- `data/events_candidates.csv` preserves all 26 original records and research notes, plus new candidates C27 and C28. Original fields are archival and may contain superseded values.
- `data/events.csv` contains the curated 20-event sample: 13 earnings, four guidance, and three macro events across seven tickers and 2019–2025.
- `data/event_review.csv` records inclusion decisions and every existing-field correction, including normalized metadata for excluded candidates.
- `data/estimates.csv` contains 13 sourced actual/consensus EPS pairs: 11 have reviewed comparable bases; C19/C25 remain unverified and are retained for qualitative analysis only.
- C12 is anchored to the export rule's October 7 public-inspection filing at 11:15 AM Eastern and is classified `intraday`.
- `data/p1_validation.csv` documents eight beat/down sign-divergence cases and three aligned comparisons (C03, C11, C23), using published next-session closing observations. These are manually supported sample roles, not computed or causally established effects.

See [the P1 review](docs/P1_REVIEW.md) for findings, sources, corrections, and the TSM exclusion from automatic EPS analysis. Database work has not started.

The database, price pipeline, reaction calculations, API, and frontend described below are the planned next stages and should not be interpreted as completed features yet.

## Research question

The current [frontend HTML draft](web/events-draft.html) can be opened directly in a browser. It preserves the supplied design and working event-type filters. Its sample rows, dates, and metrics are placeholders; it is not connected to the production dataset or an API.

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

The eligibility gate in `scripts/validate_seed.py` requires both `analysis_scope=eps_and_price` and `comparability_verified=TRUE`, finite non-null actual and consensus EPS, matching EPS bases, and matching currency, share unit, and split basis. The current estimates schema declares currency/share unit/split basis once for the pair, applying to both values; side-specific values, when supplied, must agree. `comparability_verified` controls EPS-pair admission but does not override analysis scope or missing/incompatible inputs. Event metadata verification is independent. C19/C25 remain excluded from both automatic EPS surprise and divergence.

For comparable earnings, the planned sign test compares `actual_eps - consensus_eps` with the one-day stock return. Opposite nonzero signs indicate mechanical divergence; zero or unavailable inputs produce no divergence classification. EPS surprise percentage uses `100 * (actual - consensus) / abs(consensus)`; zero consensus gives NULL percentage. This handles loss estimates without reversing beat/miss direction. These calculations belong in SQL, not the CSV validator. C16 (about -1.21%, softer outlook) and C22 (about -1.10%, overlapping Apple modem-business transaction) are weak/confounded sign-divergence cases, not evidence of the same causal strength as every other case. Five-day and SOXX-relative results are separate metrics and must not be substituted to fill the eight-case target. Guidance and concurrent news can explain a mechanical mismatch without proving the earnings caused the move.

### EPS inputs

`estimates.csv` joins on `candidate_id` and `fiscal_quarter`. It stores actual and consensus EPS, separate basis labels, currency, share unit, split basis, consensus snapshot date/kind, actual/consensus/comparison sources, a basis-review source, a comparability verification flag, and research notes. `USD` values for TSM are per ADR, not TWD per ordinary share. Historical NVIDIA values retain the share units used at each announcement; do not mix them with later split-restated EPS.

`consensus_snapshot_date` is a documentary proxy: the publication date of a preview, or the release-day results report for C22. It is not an exact analyst-vendor extraction timestamp. `snapshot_kind` distinguishes these cases. Sources come from different providers and may use different estimate panels. C01's preview was subsequently updated; contemporaneous results reporting corroborates its consensus value. These are manually researched retrospective inputs, not an immutable point-in-time feed. TSM actuals use `tifrs`; consensus basis is explicitly `unverified` and `comparability_verified=FALSE`. The TSM replacement sources have blank snapshot dates with `snapshot_kind=unverified_snapshot`; earlier Zacks sources and dates remain in their notes. `data/tsm_research.csv` preserves provisional C19/C20/C25 inputs, separate `usd_per_adr` units for actual and consensus, and reaction-window caveats. C20’s candidate pattern is corrected to aligned but it remains excluded. See the TSM supplement in the P1 review.

C22’s reported-at-release 0.89 consensus is accepted with its snapshot limitation because the EPS bases are comparable; the available pre-release 0.90 would still leave actual EPS of 1.06 classified as a beat.

C12 and C13 use reaction-day close-to-close returns that include pre-announcement trading, not pure post-announcement windows. C26 represents broad trade-policy/market sentiment; semiconductors were exempt from this reciprocal-tariff order. For SOXX macro events, use SPY/QQQ as a broader benchmark or leave excess return NULL. Never benchmark SOXX against itself. The current P1 sample adds no benchmark tickers; benchmark data collection belongs to P3.

## Planned architecture

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

No PostgreSQL schema or loader exists yet. `events.csv` has 18 columns; its header is not a seven-column import schema. P2 must use an 18-column staging table and an explicit named-column INSERT projection, retaining `analysis_scope` and verification metadata. Never positionally copy this file into a seven-column table. See [the P2 import contract](docs/P2_IMPORT_CONTRACT.md) for the exact staging order and admission rules.

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
- [ ] Create the PostgreSQL schema and seed-data import
- [ ] Collect adjusted historical prices
- [ ] Optional TSM EPS extension: reconcile two consensus bases before enabling automatic EPS analysis
- [ ] Calculate reaction and divergence metrics in SQL
- [ ] Build the FastAPI endpoints
- [ ] Connect the web interface to the validated data
- [ ] Add a full methodology page and deployment

## Responsible use

This repository is an educational event-study project. It describes historical market reactions and does not provide forecasts, personalized investment recommendations, or trading advice.
