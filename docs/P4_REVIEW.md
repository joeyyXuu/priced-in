# P4 consensus-estimate acceptance

P4 is complete for the approved retrospective sample. All 13 EPS pairs have a documented disposition: 11 accepted comparable inputs and two qualitative-only TSM pairs. No production values, sample membership, sources or eligibility flags were changed in P4. The optional TSM accounting reconciliation remains unresolved and does not block P5.

## Audit scope and findings

This phase reuses the manually sourced, human-approved P1 evidence. It reviewed all 13 records' actual/consensus values, reported quarters, accounting basis, currency, share unit, split convention, source links, publication-date proxies and caveat notes. It is not a claim that all source websites were independently re-certified in P4 or that an immutable analyst-vendor feed was obtained.

The new read-only `scripts/validate_estimates.py` compares every estimates CSV field with PostgreSQL, including both sides of each expanded currency/share-unit/split-basis field. It also compares the Python admission set with `automatic_eps_inputs` in a consistent database snapshot. All 13 mappings and the 11-record eligibility set passed. `data/p4_estimate_review.csv` is the generated row-level audit, not another production input dataset.

| Disposition | IDs | Basis and treatment |
|---|---|---|
| Accepted retrospective EPS inputs | C01, C03, C04, C09, C11, C16, C18, C22, C23, C27, C28 | Matching non-GAAP EPS, USD per diluted common share, announcement-date split units |
| Qualitative only | C19, C25 | Actual TIFRS, USD per ADR; consensus basis and replacement-source snapshot unverified |

Ten accepted records use `pre_release_publication`; C22 uses `reported_at_release`. Neither label proves an exact vendor extraction timestamp. The two TSM records retain blank snapshot dates and `unverified_snapshot`. Negative EPS in C18 is intentional and must not be zero-filled or converted to a positive value. Historical NVIDIA EPS must not be replaced by later split-restated numbers on only one side of the pair.

## Source and snapshot limitations

- **C01:** the selected preview has a later update. Its original publication date remains a documentary proxy, with the previously reviewed release-day corroboration retained. The CityNews corroboration URL returned a cache miss on the P4 spot-check; this is recorded as an access limitation, not new contrary evidence or fresh verification. The existing P1 acceptance is preserved.
- **C22:** the [Zacks-authored results comparison](https://www.investing.com/analysis/intel-intc-beats-on-earnings-in-q2-inks-deal-with-apple-200445823) was accessible and explicitly compared non-GAAP actual 1.06 with consensus 0.89. The accepted release-day snapshot remains distinct from the pre-release 0.90 preview. Both expectations are below the actual; no production surprise percentage is calculated here.
- **C11:** the [November 15, 2022 StockStory preview](https://stockstory.org/us/stocks/nasdaq/nvda/news/earnings/nvidia-nvda-to-report-earnings-tomorrow-here-is-what-to-expect) was accessible and explicitly described adjusted EPS expectations of 0.70. Its consensus evidence is in that preview; the issuer release linked as basis evidence establishes the actual result, not an independent consensus estimate.
- **C19/C25:** provisional consensus numbers remain stored for research. No new quarter-specific accounting reconciliation was established. Do not relabel TIFRS actuals as non-GAAP or use event-metadata verification to admit these pairs.
- **Other accepted records:** retain the existing P1 source review and publication-date caveats; P4 does not claim new website verification for each URL. Different providers can have different analyst panels. These limitations are acceptable for this defined retrospective study, not for claims of immutable point-in-time backtesting.

## Validation and handoff

Run from the repository root with the P2 database running:

```sh
python3 scripts/validate_estimates.py
python3 scripts/db.py test
```

The audit performs no database writes. It fails on value, unit, source, note, snapshot or eligibility drift. Regression tests cover numeric equivalence and rejection of changed consensus, units, provenance, dates and verification. Existing P1, P3 and database tests remain in the full suite.

P5 can now compute financial metrics in PostgreSQL using `automatic_eps_inputs` for EPS admission. It must retain all 20 events for appropriate price/qualitative analysis, leave automatic EPS metrics unavailable for blocked or out-of-scope events, use absolute consensus in the percentage denominator with zero-consensus protection, and reconcile computed adjusted reactions against P1 observations without forcing the original eight-case count.
