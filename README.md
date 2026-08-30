# Priced In

**When a beat still sinks the stock.**

Priced In is a retrospective semiconductor event-study project that examines why a stock can fall after apparently strong earnings—and why it can rise after weak results. It connects reported performance and management guidance with the market's actual reaction.

The project is intentionally narrow: semiconductor-related events from 2019–2025, a small group of companies, and a manually reviewed dataset. It is not a prediction tool, a trading signal, or a real-time market-data product.

## Project status

The project is currently in the data-validation stage.

- `data/events.csv` contains 26 candidate events across seven tickers.
- Announcement dates, release timing, event type, and sources have been reviewed.
- 25 rows are currently verified.
- Candidate `C12` has a confirmed announcement date but remains unverified because an authoritative publication timestamp was not available.
- The candidate pool will be reduced to a final sample of approximately 20 events before reaction metrics are calculated.

The database, price pipeline, reaction calculations, API, and frontend described below are the planned next stages and should not be interpreted as completed features yet.

## Research question

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

The events are manually selected rather than randomly sampled. The candidate pool is designed to include potential expectation/reaction divergences, ordinary control cases, and macro events that affected the semiconductor sector without a company earnings release.

## Data dictionary

| Column | Description |
|---|---|
| `candidate_id` | Stable identifier used while reviewing the candidate pool. |
| `ticker` | Company ticker or `SOXX`, used as the semiconductor-sector proxy. |
| `approx_period` | Approximate month originally used to locate the event. |
| `event_date` | Actual announcement date in `YYYY-MM-DD` format. |
| `release_timing` | `bmo` = before market open, `amc` = after market close, `intraday` = during market hours. |
| `event_type` | Primary event category: `earnings`, `guidance`, `macro`, or `product`. |
| `fiscal_quarter` | Fiscal quarter reported or discussed; blank for events where it does not apply. |
| `expected_pattern` | Pre-analysis hypothesis: `aligned`, `divergent`, or `macro`. It is not the calculated result. |
| `why_selected` | Short explanation of why the event belongs in the candidate pool. |
| `recall_confidence` | Initial confidence in the candidate description before full validation. |
| `source_url` | Source used to validate the event. |
| `verified` | Whether the date, source, and timing have been sufficiently validated. |

### What “guidance” means

Guidance is management's forward-looking outlook, such as expected revenue, margins, EPS, or demand for a future quarter or year. It is different from both the results already reported and analysts' consensus estimates. An event is labelled `guidance` when the forward outlook is the main reason the event was selected.

## Reaction-day methodology

`event_date` is the announcement date, but it is not always the correct market-reaction date.

| Release timing | Reaction-day convention |
|---|---|
| `bmo` | First trading day on or after `event_date`. |
| `amc` | First trading day after `event_date`. |
| `intraday` | First trading day after `event_date` under the current daily-close methodology. This avoids measuring a close-to-close return that partly occurred before the announcement; intraday data would be needed for a more precise same-day window. |

This distinction prevents an after-hours earnings release from being matched to a return that occurred before the information became public.

The planned SQL layer will use trading-day indices and a per-event `LATERAL JOIN` to locate the appropriate reaction date. A 60-trading-day volume baseline will exclude the event day to avoid look-ahead bias.

## Planned metrics

- EPS surprise percentage
- One-day and five-day price reaction
- One-day excess return relative to SOXX
- Event-day volume relative to the prior 60-trading-day average
- Divergence between the earnings surprise and share-price direction

EPS actuals and consensus estimates will use one consistent basis—preferably non-GAAP—because mixing GAAP and non-GAAP values can create misleading surprise percentages.

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

Clone the repository and load the CSV with any standard data tool. For example:

```python
import pandas as pd

events = pd.read_csv("data/events.csv", parse_dates=["event_date"])
verified_events = events[events["verified"]]

print(verified_events["release_timing"].value_counts())
```

Before treating the file as the final research sample:

1. Resolve or remove any row where `verified` is `FALSE`.
2. Reduce the candidate pool to the documented final selection.
3. Preserve source links and do not change classifications to force a more interesting result.
4. Keep earnings actuals and consensus estimates on the same GAAP or non-GAAP basis.

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
- [ ] Resolve the remaining unverified timing record and select the final sample
- [ ] Create the PostgreSQL schema and seed-data import
- [ ] Collect adjusted historical prices
- [ ] Add consistent consensus and actual EPS data
- [ ] Calculate reaction and divergence metrics in SQL
- [ ] Build the FastAPI endpoints
- [ ] Connect the web interface to the validated data
- [ ] Add a full methodology page and deployment

## Responsible use

This repository is an educational event-study project. It describes historical market reactions and does not provide forecasts, personalized investment recommendations, or trading advice.
