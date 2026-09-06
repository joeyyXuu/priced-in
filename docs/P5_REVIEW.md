# P5 calculations and SQL walkthrough

P5 calculates all 20 events from the P3 adjusted-price inputs, admitting 11 EPS pairs through the P4 eligibility gate. Eight calculated one-day patterns are divergent and three aligned. All 11 match P1's reaction dates and patterns; the largest absolute difference from a source-reported one-day return is approximately 0.0413 percentage points (C27). The 0.10-point reconciliation threshold is a review aid, not a statistical significance threshold.

## Run and review

```sh
python3 scripts/metrics.py
python3 scripts/test_metrics.py
```

Read `data/p5_metrics.csv` for the complete operands and calculated outputs; `data/p5_reconciliation.csv` compares the 11 eligible cases with P1 evidence. All financial arithmetic and reconciliation differences run in SQL. Python invokes PostgreSQL and exports results.

`db/04_metrics.sql` builds three ordinary views and refreshes one materialized view inside a transaction. Ordinary views execute their query when read; a materialized view stores the resulting rows. `event_metrics` is the persisted snapshot for future API reads. Re-run the metrics command after changing prices or estimates: materialized results do not refresh automatically. The acceptance checks reject incomplete input coverage but never require the original eight divergence count. Future incompatible schema changes require a migration.

## 1. Give market sessions sequence numbers

```sql
SELECT price_date,
       row_number() OVER (ORDER BY price_date) AS session_no
FROM prices WHERE ticker = 'SPY';
```

`ROW_NUMBER` numbers rows in date order. The P3-validated SPY dates supply a common US session calendar. Crossing those dates with tickers preserves a missing company price as NULL instead of skipping to the next date. Revalidate P3 coverage after a price refresh: deleting a date from the calendar itself could otherwise affect every ticker.

`trading_prices` then partitions window functions by ticker. `LAG(adjusted_close)` retrieves the preceding session's close; `LEAD(adjusted_close, 4)` retrieves the fifth session counting the current session as day one. Five-day completeness requires all five closes.

```sql
AVG(volume) OVER (
  PARTITION BY ticker ORDER BY session_no
  ROWS BETWEEN 60 PRECEDING AND 1 PRECEDING
)
```

This frame excludes the reaction day and requires 60 observed volumes. For an after-close release, the announcement day's trading is before the reaction session and is included in the baseline. This is a reaction-day volume measure; it does not assert that the baseline contains no anticipatory trading.

## 2. Find each event's reaction session

`event_metric_inputs` uses `LEFT JOIN LATERAL`: the query on the right can refer to the current event on the left.

```sql
WHERE p.ticker = e.ticker
  AND (p.price_date > e.event_date
       OR (p.price_date = e.event_date AND e.release_timing <> 'amc'))
ORDER BY p.session_no
LIMIT 1
```

An `amc` release starts strictly after announcement day. `bmo` and `intraday` can start on the same day. Left joins keep all events visible even when an input is missing. The benchmark uses the exact same dates, with SOXX for company events and SPY for SOXX macro events.

## 3. Calculate metrics

| Output | SQL arithmetic | Meaning |
|---|---|---|
| EPS surprise % | `100*(actual_eps-consensus_eps)/NULLIF(ABS(consensus_eps),0)` | Positive means better EPS than expected, including smaller losses |
| One-day return % | `100*(reaction_close/NULLIF(previous_close,0)-1)` | Previous session close to reaction session close |
| Five-day return % | `100*(fifth_close/NULLIF(previous_close,0)-1)` | Same baseline through reaction day plus four sessions |
| Excess return, percentage points | `return_1d_pct-benchmark_return_1d_pct` | Difference from benchmark performance; not a fitted abnormal return |
| Volume multiple | `reaction_volume/NULLIF(prior_volume_avg,0)` | 2 means twice the prior 60-session average |

`NULLIF(x,0)` turns zero into NULL, preventing division by zero. A zero-consensus case has no EPS percentage but may still have a nonzero EPS difference for the sign test. C18 demonstrates the loss convention: actual -1.07 versus expected -1.18 gives +9.3220%, a smaller loss than expected.

The SQL joins EPS only through `automatic_eps_inputs`. Guidance, macro, and qualitative TSM rows keep their price metrics but receive NULL EPS operands, surprises and automatic classifications. Provisional TSM values remain in `estimates`; a blank calculated metric does not mean zero.

## 4. Classify the one-day signs

Opposite nonzero signs of `actual_eps-consensus_eps` and `return_1d_pct` produce `divergent`; matching signs produce `aligned`. Missing, ineligible or zero-sign inputs produce NULL. Five-day and benchmark-relative returns are separate outputs and do not replace this fixed sign test. There is no materiality threshold or claim that EPS caused the move.

| Event | EPS surprise % | One-day % | Five-day % | One-day excess, pp | Pattern |
|---|---:|---:|---:|---:|---|
| C04 NVDA | 6.2500 | -6.3848 | -14.6485 | -6.0971 | Divergent |
| C03 NVDA | 29.1866 | 0.0997 | 4.5589 | 3.4047 | Aligned |
| C11 NVDA | -17.1429 | -1.4645 | 3.8278 | -2.2477 | Aligned |
| C18 MU | 9.3220 | -4.4128 | -0.1466 | -6.2645 | Divergent |

C11 illustrates horizon sensitivity: a miss/down classification on day one coexists with a positive five-day return. C03 illustrates relative performance: a small positive stock return can exceed a falling benchmark by several percentage points.

## Findings, caveats and tests

The eight calculated divergences are C01, C04, C09, C16, C18, C22, C27 and C28; comparisons C03, C11 and C23 are aligned. C16 and C22 remain small, confounded mismatches. These are observations from a purposively selected sample, not an unbiased estimate of how frequently earnings beats cause declines.

C19's computed closing-session return is +9.7930%. The earlier qualitative research claim of more than 11% was not a verified identical closing window; do not replace this computed return with that headline figure. C25's closing return is +3.8636%. Both remain excluded from automatic EPS metrics. Intraday macro returns include pre-announcement trading. Adjusted closes and provider volume retain the P3 caveats, including split-sensitive volume comparisons and possible retrospective provider revisions.

Four live SQL tests passed: a hand-calculated fixture checks EPS 50%, returns 10%/20%, excess 5/10 points and volume 2x; loss/zero/equal EPS tests check null and sign behavior; a missing price test confirms the reaction date does not shift; and snapshot/scope checks compare stored and live results. All fixture mutations roll back. The existing 22 regression tests also pass. No production seed or price inputs were modified by P5.

P6 can read the persisted metrics through a read-only API without external provider requests at request time.
