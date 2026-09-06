# Frontend integration

The supplied HTML design now displays live responses from the local API. All fabricated event rows, dates, percentages, and narrative labels have been removed. The implementation uses HTML, CSS and JavaScript; a React migration is not part of this connection change.

## Open the application

```sh
python3 scripts/setup_api.py
```

Visit http://127.0.0.1:8000/. The API container includes `web/` and serves the page plus `/assets/events.js`. Rebuild with the same command after frontend changes. Open the served URL rather than the HTML file on disk: requests such as `/events` need the running service. API documentation remains at `/docs`.

## What is connected

- `/filters` supplies actual event types, tickers and years. `/events` supplies the total sample count and event rows with SQL metrics. There is no sample-data fallback.
- Type, ticker, year and calculated-pattern filters are sent to the API. Changing filters cancels previous list requests so older responses cannot overwrite a newer selection. The current 20-event sample is fetched with the API's 100-row limit; pagination will be needed if the sample expands beyond that limit.
- Selecting a headline requests the event detail and its price window. The dialog displays announcement/reaction dates, EPS and price metrics, benchmark excess return, volume multiple, research reasoning, timing notes, EPS provenance and source links.
- Price tables display five sessions before the reaction and five including it, for both the event ticker and benchmark. Prices and financial metrics are displayed from API values, with formatting only in JavaScript.
- Unavailable EPS values are dashes, never fabricated zeros. Guidance, macro and unverified TSM cases have no automatic EPS classification. Provisional TSM actual/consensus values appear in the detail's research section with accounting labels and verification status.
- Loading, empty, failed-list and failed-detail states are explicit. Retry requests real data again. No previous rows remain visible as if a failed request succeeded.

The page retains the original paper-toned design, adds a mobile card layout, native keyboard-accessible controls and a modal dialog, and renders API text using `textContent`. External source links are restricted to HTTPS and open with `noopener noreferrer`.

## Validation

Real Chrome browser checks passed against the running API: 20 loaded rows, type/ticker/pattern filters, TSM null EPS, detail prices, SPY macro benchmark, empty results, forced API failure and recovery, and no JavaScript page errors. Mobile layout was inspected. The existing seven API tests also passed. Browser testing used temporary Playwright tooling outside the repository.

Production CSVs and database metrics are unchanged. Data collection and SQL snapshot refresh remain separate commands; opening the page does not contact Yahoo or recalculate metrics.
