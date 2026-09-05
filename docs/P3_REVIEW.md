# P3 historical price review

P3 price ingestion is complete for the approved 20-event sample. PostgreSQL contains 12,448 rows: 1,556 sessions each for AMD, AVGO, INTC, MU, NVDA, SOXX, SPY and TSM, covering February 25, 2019 through May 1, 2025. Production seed CSVs and EPS eligibility are unchanged.

## Collection and reproducibility

`scripts/prices.py` uses Yahoo Finance through yfinance. The [provider client documentation](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html) specifies an exclusive end date and configurable adjustment/action options. Requests explicitly use daily data, `auto_adjust=False`, `back_adjust=False`, `repair=False`, and `actions=True`; `Adj Close` goes into PostgreSQL, while OHLC, dividends and split records remain in local snapshots. No silent repair or forward fill occurs.

`requirements-prices.txt` records the working Python 3.9 environment, separately from the original application requirements. That interpreter resolves yfinance 1.2.0 and exchange-calendars 4.5.6. Its system LibreSSL causes an urllib3 compatibility warning; actual Yahoo downloads succeeded through curl_cffi. A newer Python environment should be validated before changing these pins.

Ignored `data/prices/` holds per-ticker CSVs, SHA-256 hashes, retrieval timestamps, requested bounds and client versions. Repeated runs reuse these snapshots and preserve retrieval dates. `--refresh` explicitly downloads new snapshots; providers can retrospectively revise adjustments. Each database row retains source/client version and retrieval time. These are retrospective observations, not a point-in-time market feed. Raw files remain local, not published in Git.

## Coverage and quality

All 20 events have the preceding close, 60 sessions before the reaction day and five reaction sessions. `data/p3_coverage.csv` records the dates and selected benchmark. Company events use SOXX; SOXX macro events use SPY. The calendar verifies holidays and gaps independently of the downloaded rows, so missing rows cannot silently move reaction dates. No required or full-range sessions are missing; no duplicate, nonfinite/nonpositive price or nonpositive/fractional volume rows passed admission.

The installed calendar predates the January 9, 2025 Carter mourning closure. An explicit exception is supported by the [NYSE closure announcement](https://www.nasdaq.com/press-release/new-york-stock-exchange-will-close-markets-january-9-honor-passing-former-president) and [Nasdaq trader notice](https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2024-87). The requested end date is excluded from the expected sessions as well as from downloads.

`data/p3_quality.json` records the downloaded split actions: NVDA 4:1 on July 20, 2021 and 10:1 on June 10, 2024; AVGO 10:1 on July 15, 2024; SOXX 3:1 on March 7, 2024. These are provider records, not independent corporate-action certification. The volume screen found no daily volume above ten times the prior 60-session median. This broad outlier screen is not a guarantee that every value is correct.

Adjusted closes incorporate provider adjustments; do not adjust them for splits again. Volume is retained exactly as returned by Yahoo, without claiming it is independently verified as contemporaneous raw share volume. Later volume metrics must retain that convention and review split-sensitive windows. TSM prices are for the US-listed TSM ADR, not Taiwan ordinary shares. Adjusted-price reactions may differ from the unadjusted/source-rounded P1 observations and require reconciliation in the SQL phase.

## Validation and next phase

The pipeline verifies every imported price and volume against PostgreSQL after its transactional upsert. A repeated cached import succeeded with 12,448 rows and no duplicates. Offline tests cover timing, benchmark choice, missing sessions, invalid values and duplicate rejection. P1 and database acceptance checks still pass.

P3 supplies inputs and coverage dates only. SQL remains responsible for production returns, EPS surprises, volume metrics and divergence classification. C19/C25 remain blocked from automatic EPS calculations. The next implementation work can build the SQL reaction layer against these validated inputs.
