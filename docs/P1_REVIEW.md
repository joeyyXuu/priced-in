# P1 selection and input review

Final seed review: September 5, 2026. **P1 is complete for the defined production sample.** Published closing-session evidence supports eight mechanical EPS/price sign-divergence cases and three aligned comparisons. All 20 events have reviewed announcement metadata. C19 and C25 remain in the sample for qualitative analysis only, with unverified EPS comparability explicitly excluded from automatic calculations. Their unresolved accounting reconciliation is not represented as verified. P2 PostgreSQL setup is now implemented and tested; the approved P1 CSVs and sample composition are unchanged. See the [P2 import contract](P2_IMPORT_CONTRACT.md). Production prices and metrics remain P3/P5 work.

## Sample

The 20 selected events cover all seven tickers and every year from 2019 through 2025. They comprise 13 earnings, four guidance, and three macro events. C27 and C28 were added to research to address the original pool's shortage of defensible earnings-divergence candidates; C05 and C17 give up their sample slots. All original 26 records and research notes remain in `events_candidates.csv`, followed by the two new records. The user-authorized TSM supplement corrects C20’s candidate `expected_pattern` from `divergent` to `aligned`; its original `why_selected` is preserved as superseded research reasoning. Archive labels are historical research, not current truth. `event_review.csv` records normalized metadata for all 28 and every change to an existing production field.

| ID | Ticker | Announcement | Reported quarter | Role |
|---|---|---|---|---|
| C01 | INTC | 2020-07-23 | FY20Q2 | Divergence candidate |
| C02 | NVDA | 2023-05-24 | FY24Q1 | Qualitative guidance |
| C03 | NVDA | 2023-08-23 | FY24Q2 | Designated comparison: beat/up; muted positive reaction |
| C04 | NVDA | 2024-08-28 | FY25Q2 | Divergence candidate |
| C06 | AVGO | 2024-12-12 | FY24Q4 | Qualitative guidance |
| C07 | MU | 2024-12-18 | FY25Q1 | Qualitative guidance |
| C09 | NVDA | 2025-02-26 | FY25Q4 | Divergence candidate |
| C10 | INTC | 2024-01-25 | FY23Q4 | Qualitative guidance |
| C11 | NVDA | 2022-11-16 | FY23Q3 | Designated comparison: miss/down |
| C12 | SOXX | 2022-10-07 | — | Macro: export controls |
| C13 | SOXX | 2022-09-21 | — | Macro: Federal Reserve rate decision |
| C16 | AMD | 2022-08-02 | FY22Q2 | Divergence candidate |
| C18 | MU | 2023-09-27 | FY23Q4 | Divergence candidate |
| C19 | TSM | 2024-10-17 | FY24Q3 | Qualitative earnings context; automatic EPS excluded |
| C22 | INTC | 2019-07-25 | FY19Q2 | Divergence candidate |
| C23 | NVDA | 2021-11-17 | FY22Q3 | Designated comparison: beat/up |
| C25 | TSM | 2025-01-16 | FY24Q4 | Qualitative earnings context; automatic EPS excluded |
| C26 | SOXX | 2025-04-02 | — | Macro: reciprocal-tariff announcement |
| C27 | NVDA | 2023-11-21 | FY24Q3 | New divergence candidate |
| C28 | MU | 2024-06-26 | FY24Q3 | New divergence candidate |

The eight supported sign-divergence cases are C01, C04, C09, C16, C18, C22, C27, and C28. Each has comparable sourced non-GAAP EPS and published evidence of a negative next-session close-to-close move after a beat. All eight are beat/down cases; no reverse miss/up case is established. No guidance or macro event fills the EPS quota. The three comparisons are now **C03, C11, and C23**, replacing the unverified C25 EPS comparison with C03 from the existing sample. “Ordinary” means conventional aligned direction here, not matched or low-volatility controls: C03 had a very large EPS beat and C23 a large gain. All three comparisons are NVIDIA, a concentration limitation. Production adjusted-return calculations remain P3/P5 work and must be reconciled against these manual source observations.

## Exclusions

| ID | Reason |
|---|---|
| C05 | Large restructuring and dividend-suspension selloff is not an ordinary control; replaced to make room for earnings-divergence coverage. |
| C08 | January 27 marks the DeepSeek selloff, while the identified R1 release was January 20. No verified January 27 publication anchor supports the current announcement-date methodology. |
| C14 | Acquisition, not product launch; simultaneous earnings and deal effects complicate attribution. |
| C15 | Overlapping AI-guidance case; positive next-session reaction does not establish EPS divergence. |
| C17 | Redundant memory-downcycle guidance case; C07 retains that context. |
| C20 | Positive US ADR reaction does not support the original divergence narrative; CPI-driven market reversal is a confounder. |
| C21 | Research note conflates January's guidance reduction with February's earnings release; C22 retains 2019 coverage. |
| C24 | Positive next-session close does not support the original divergence hypothesis; VMware context overlaps C06. |

DeepSeek's [official release history](https://api-docs.deepseek.com/news/news250120/) identifies January 20. AMD's [acquisition announcement](https://ir.amd.com/news-events/press-releases/detail/977/amd-to-acquire-xilinx-creating-the-industrys-high-performance-computing-leader) supplies the corrected C14 category and source. Exclusions preserve the research and can be reconsidered with better evidence or a separately defined episode study.

## Timing and field corrections

- Every production company quarter uses `FYxxQx`. The archive preserves original formatting, while the review log has normalized values even for excluded records. Macro and acquisition quarters stay blank. The field denotes the reported quarter, so guidance's future target period must be recorded separately if quantitative guidance analysis is added. Fiscal labels are not calendar years: C02 is FY24Q1 announced in May 2023; C25 is FY24Q4 announced in January 2025.
- Every production record gains a factual `headline`, timing evidence/notes, and a selection role. Interpretations remain in `why_selected`. `verified` verifies event metadata, not EPS comparability or reaction direction.
- C02: replace “datacenter guidance” with company-wide revenue outlook. C10: replace “in line” with an adjusted EPS beat accompanying weak guidance.
- C03 and C11: change `expected_pattern` from divergent to aligned. A muted positive move and an initial after-hours rise are not next-session beat/down and miss/up evidence respectively.
- C16 and C22: change aligned to a divergent hypothesis. C16's “PC demand collapse showed up in results” is replaced with a beat plus softer outlook; C22 is not retained as an ordinary control.
- C18: replace the vague prior stock-turn narrative with a smaller-than-expected loss and subsequent decline; retain weak-guidance context.
- C14: reviewed category becomes `acquisition`; replace the redirecting source URL. C09 uses the complete timestamped issuer-distributed release URL; C16 uses AMD's current investor-relations release. Original URLs remain archived.
- C19/C25: explicitly identify USD per US ADR and unresolved consensus basis; set `analysis_scope=qualitative` and `sample_role=qualitative`. C03 becomes a designated comparison in C25’s place. C23: qualify the ordinary-comparison description. C26: describe broad policy exposure, not a direct chip tariff. All production rows now have an explicit analysis scope, recorded in the review notes.

C12 is now `intraday`, with `verified=TRUE`: the [official Federal Register document](https://www.govinfo.gov/content/pkg/FR-2022-10-13/pdf/2022-21658.pdf), final page, records public-inspection filing on October 7 at 11:15 AM. The [National Archives explains Eastern-time inspection timestamps](https://www.archives.gov/federal-register/public-inspection). This verifies public availability of the actual rule, not the precise publication time of the original BIS press webpage. Its formal October 13 publication date does not replace the October 7 announcement anchor.

C13 is anchored to the [Fed's 2 PM EDT release](https://www.federalreserve.gov/newsevents/pressreleases/monetary20220921a.htm). C26 uses the [official remarks transcript's 4:06 PM April 2 speech start](https://www.presidency.ucsb.edu/documents/remarks-announcing-additional-united-states-tariff-actions-foreign-imports); April 3 is the transcript's release date. The [tariff order](https://www.whitehouse.gov/presidential-actions/2025/04/regulating-imports-with-a-reciprocal-tariff-to-rectify-trade-practices-that-contribute-to-large-and-persistent-annual-united-states-goods-trade-deficits/) exempts semiconductors from these reciprocal tariffs.

Issuer-distributed earnings-release timestamps and issuer footers support the other session classifications. Intel's 16:00 release-footers are corroborated by after-close schedules for [2019](https://www.intc.com/news-events/press-releases/detail/1091/intel-reports-first-quarter-2019-financial-results) and [2020](https://www.intc.com/news-events/press-releases/detail/1086/intel-reports-first-quarter-2020-financial-results). TSM's public calls establish availability before the US open; exact press-release times are left blank. All record-level timing sources are in `events.csv`.

## EPS inputs and the TSM disposition

| ID | Actual EPS | Consensus EPS | Documentary snapshot date | Status |
|---|---:|---:|---|---|
| C01 | 1.23 | 1.11 | 2020-07-19 | Comparable non-GAAP; subsequently updated preview |
| C03 | 2.70 | 2.09 | 2023-08-22 | Comparable non-GAAP |
| C04 | 0.68 | 0.64 | 2024-08-28 | Comparable non-GAAP; pre-close preview |
| C09 | 0.89 | 0.84 | 2025-02-25 | Comparable non-GAAP |
| C11 | 0.58 | 0.70 | 2022-11-15 | Comparable non-GAAP |
| C16 | 1.05 | 1.03 | 2022-08-02 | Comparable non-GAAP; 15:30 ET preview |
| C18 | -1.07 | -1.18 | 2023-09-20 | Comparable non-GAAP; smaller loss is a beat |
| C19 | 1.94 | 1.79 | Unverified for replacement source | BLOCKED: provisional FactSet/IBD input; TIFRS actual |
| C22 | 1.06 | 0.89 | 2019-07-25 | Comparable non-GAAP; release-day reporting proxy |
| C23 | 1.17 | 1.11 | 2021-11-14 | Comparable non-GAAP |
| C25 | 2.24 | 2.16 | Unverified for historical table | BLOCKED: MarketBeat numeric pair; TIFRS actual |
| C27 | 4.02 | 3.36 | 2023-11-21 | Comparable non-GAAP; morning preview |
| C28 | 0.62 | 0.48 | 2024-06-19 | Comparable non-GAAP |

Each pair's actual, consensus, and comparison citations are stored in `estimates.csv`; decimal values are USD in announcement-date share units. C19 and C25 must not be relabelled non-GAAP solely because a data provider calls earnings “adjusted.” Obtain explicit provider accounting-basis documentation, or another genuinely comparable pair, before setting their comparability flags to TRUE.

C22's [release-day report](https://finance.yahoo.com/news/intel-q2-earnings-2019-185932943.html) explicitly compares adjusted 1.06 with 0.89. A [pre-release Nasdaq preview](https://www.nasdaq.com/articles/intel-intc-2nd-quarter-earnings%3A-what-to-expect-2019-07-25) used 0.90. The selected 0.89 is labelled `reported_at_release`, not falsely presented as an independently archived pre-release observation. For C01 the preview displays a later update, so the consensus is cross-checked against contemporaneous results reporting. Every preview date is a documentary proxy, not a verified vendor database extraction time; immutable point-in-time research would require additional archived snapshots for all pairs.

All eight cases now have manually reviewed published observations for the same one-day window in `data/p1_validation.csv`. Historical reporting supports the newly added [C27 decline](https://www.shorenewsnetwork.com/2023/11/22/wall-st-closes-higher-4/) and [C28 decline](https://www.latimes.com/business/story/2024-06-27/stock-market-today-wall-street-inches-higher-ahead-of-inflation-report). C16 and C22 are especially sensitive to small moves and confounders; neither should be called a meaningful earnings-driven divergence solely from opposite signs. C11's after-hours rise versus next-session decline is another reason to validate a fixed daily window. Source-reported percentages are stored only in the P1 evidence log, never as calculated production results.

P1 acceptance now rests on the 11 comparable earnings cases and the verified metadata of the remaining nine events. C19/C25 are explicitly outside automatic EPS analysis rather than unverified members of the required comparison group. This satisfies the seed-selection criteria without claiming that all 13 EPS pairs are verified. P4 remains incomplete for the optional TSM EPS extension. P2 may proceed. The validator checks cross-file integrity, analysis-scope restrictions, and the eight-plus-three evidence coverage; it does not independently certify source truth or implement the financial metric pipeline.


## Final P1 evidence and acceptance

`data/p1_validation.csv` contains source URLs, reaction dates, source-reported percentages, evidence types, and confounder notes for the 11 automatic EPS cases. All use the US close immediately before the reaction session to that session's close; all 11 happen to be after-close releases followed by a next-calendar-day trading session. The macro reaction anchors remain October 7, 2022 (C12), September 21, 2022 (C13), and April 3, 2025 (C26). Macro direction is not used to fill an EPS quota.

| ID | Reaction session | EPS result | Published session move | Manual finding |
|---|---|---|---:|---|
| C01 | 2020-07-24 | Beat | -16.24% | Sign divergence; 7nm delay confounds attribution |
| C04 | 2024-08-29 | Beat | -6.38% | Sign divergence; forward expectations matter |
| C09 | 2025-02-27 | Beat | -8.5% | Sign divergence; margin outlook and broader weakness |
| C16 | 2022-08-03 | Beat | -1.21% | Small sign divergence; softer outlook |
| C18 | 2023-09-28 | Smaller loss than expected | -4.4% | Sign divergence; weak profitability outlook |
| C22 | 2019-07-26 | Beat | -1.1% | Small sign divergence; concurrent modem-business sale |
| C27 | 2023-11-22 | Beat | -2.5% | Sign divergence; China sales restrictions |
| C28 | 2024-06-27 | Beat | -7.1% | Sign divergence; forecast disappointment |
| C03 | 2023-08-24 | Beat | +0.1% | Aligned comparison; muted gain still has positive sign |
| C11 | 2022-11-17 | Miss | -1.5% | Aligned comparison; initial after-hours rise is excluded |
| C23 | 2021-11-18 | Beat | +8.25% | Aligned comparison; not a low-volatility control |

These percentages are transcribed at each source's precision; no return calculation was moved from SQL into Python. They are ordinary published stock moves, not a verified adjusted-total-return series. P3 must collect adjusted price data and corporate actions, and P5 must compute the actual metrics. A discrepancy must trigger review rather than changing the window or manufacturing a result to preserve the quota. A mechanical sign mismatch does not prove a meaningful or earnings-caused effect; the project must retain guidance and macro context.

The TSM investigation confirmed the issuer's Q3 and Q4 actuals, their ADR units, and the published consensus numbers. The [issuer's Q4 earnings release](https://investor.tsmc.com/english/encrypt/files/encrypt_file/reports/2025-01/cc4e1dec3474f69109d5455fbf8939c3e3cd5a71/4Q24EarningsRelease.pdf) explicitly identifies consolidated TIFRS. [Zacks' own methodology](https://zacksdata.com/consensus/faq/) distinguishes adjusted Street and BNRI estimates. Its [Q4 comparison](https://www.zacks.com/stock/news/2402068/taiwan-semiconductor-manufacturing-company-ltd-tsm-hit-a-52-week-high-can-the-run-continue) confirms the selected numbers but supplies no quarter-specific bridge from those adjustments to TIFRS. Therefore both `comparability_verified` flags stay FALSE and `consensus_eps_basis` stays `unverified`. The investigation is closed for P1 with an explicit qualitative-only disposition; upgrading either row later requires actual reconciliation evidence.

Acceptance checks: 20 production events; 28 preserved research candidates with original research notes preserved and the explicitly requested C20 pattern correction; seven tickers; all years 2019–2025 represented; three macro events; eight supported sign-divergence cases; three supported aligned comparisons; no automatic EPS use of qualitative or macro cases. Source snapshot limitations for C01 and C22 remain disclosed. No commitments about causal significance, low-volatility controls, or immutable point-in-time consensus data are made.


## User-supplied TSM supplement

This supplement changes only TSM research inputs and their validation. The final 20 event IDs, eight supported divergence cases, three designated comparisons, and macro sample remain unchanged. `events.csv` and `p1_validation.csv` need no changes. C20 remains excluded; adding it would require proposing a sample change first.

| ID | Actual / consensus, USD per ADR | Supplied indicative EPS difference | Disposition |
|---|---|---|---|
| C20 | 1.79 / 1.68 | +6.55% | Correct candidate and reviewed pattern to aligned; remain excluded |
| C19 | 1.94 / 1.79 | +8.38% | Replace selected Zacks 1.74 with provisional user-supplied FactSet/IBD 1.79; qualitative aligned |
| C25 | 2.24 / 2.16 | +3.70% | Values unchanged; MarketBeat becomes selected consensus source; qualitative aligned |

`data/tsm_research.csv` stores these three provisional pairs, supplied percentages, explicit `actual_eps_unit=usd_per_adr` and `consensus_eps_unit=usd_per_adr`, price observations, source URLs, and source-access limitations. These are research claims, not accepted SQL EPS surprises: accounting comparability remains unverified. `estimates.csv` continues to contain only selected earnings events, so C20 is not added there.

All three actuals use **`tifrs`**, not `non_gaap`; consensus basis stays **`unverified`**, and **`comparability_verified=FALSE`**. For the two selected records, `currency=USD` plus `share_unit=adr` expresses the same units; validation cross-checks them against the two explicit unit fields in the supplement. Historical generic `ifrs` labels in the review notes describe earlier work; the current EPS fields now use the precise `tifrs` value.

Source verification and reaction-window findings:

- C20: [TSMC’s release](https://pr.tsmc.com/english/news/2965) supplies the actual. The accessible [Seeking Alpha transcript](https://seekingalpha.com/article/4546344-taiwan-semiconductor-manufacturing-company-limited-tsm-q3-2022-earnings-call-transcript) did not expose the supplied 1.68 consensus; retain it as user-supplied provisional research. [StatMuse](https://www.statmuse.com/money/ask/tsm-stock-price-in-oct-2022) displays 60.84 for October 12 and 63.22 for October 13, supporting the supplied approximately +3.91% direction. The provider’s price-adjustment convention was not independently established; do not mix these levels with another series. The original divergent narrative is superseded.
- C19: the [official PDF](https://investor.tsmc.com/chinese/encrypt/files/encrypt_file/reports/2024-10/d00bfb55ffe01e36f56863f975e88d827f9943e8/3Q24EarningsRelease.pdf) confirms the actual and TIFRS reporting. The accessible [IBD excerpt](https://www.investors.com/news/technology/tsm-stock-taiwan-semiconductor-q3-2024-earnings/) identifies FactSet but truncates before the consensus value. Store the user’s 1.79 provisionally; do not claim independently verified access to that figure or snapshot. This is a provider change, not evidence that Zacks’ earlier 1.74 was incorrect. The supplied [Reuters URL](https://www.reuters.com/technology/us-chip-stocks-rally-tsmcs-ai-backed-outlook-impresses-investors-2024-10-17/) was inaccessible in this review. Preserve the supplied **more-than-11%** move as an unspecified post-announcement observation, not a closing return: a separate [Reuters closing recap](https://www.investing.com/news/stock-market-news/futures-rise-as-chip-stocks-rally-after-tsmc-results-economic-data-in-focus-3667855) reports **+9.8%** for the US-listed shares.
- C25: [TSMC](https://pr.tsmc.com/english/news/3201) and [MarketBeat’s historical earnings table](https://www.marketbeat.com/stocks/NYSE/TSM/earnings/) confirm 2.24 actual / 2.16 consensus. MarketBeat’s generic GAAP actual column does not disclose the consensus accounting basis. The user’s approximately +3.9% reaction has no dedicated price citation in the supplement and remains an unverified, unspecified-window claim.

The previous Zacks sources and snapshot dates are preserved in the two estimates’ notes. Do not carry those dates onto different sources: replacement-source `consensus_snapshot_date` is blank and `snapshot_kind=unverified_snapshot`. The validator permits that combination only for blocked inputs. It also checks TIFRS, both ADR units, candidate/review alignment, consistency with selected EPS rows, and C20’s exclusion. Numerical-source verification is explicitly separate from accounting-basis verification.

**P1 remains complete for its unchanged, restricted sample, and P2 can proceed.** This supplement neither promotes TSM into automatic EPS analysis nor changes the supported eight-plus-three evidence set. No financial metrics were computed in Python, and no commit or push was performed.


## Final human-review hardening

The user approved the existing 20-event membership. No event was added, removed, or replaced. The exact role counts remain eight divergence candidates, three aligned comparisons, three macro events, and six qualitative events. Annual counts are 2019: 1, 2020: 1, 2021: 1, 2022: 4, 2023: 4, 2024: 6, 2025: 3. This is a purposive sample covering all seven years with greater weight on the recent AI cycle, not a balanced panel or a minimum-two-per-year sample. No project-plan file or existing minimum-two-per-year claim was found.

C12 retains the GovInfo PDF as its underlying rule source. Its timing evidence now points specifically to the [October 7 public-inspection list](https://www.federalregister.gov/public-inspection/2022/10/07), which lists document 2022-21658 filed at 11:15 a.m. on October 7. The October 11 list is not the timing source. The review log records the same evidence URL.

C16 and C22 remain among the eight mechanical beat/down cases but are explicitly weak/confounded: the reported declines are approximately 1.21% and 1.10%, with softer outlook and the Apple modem-business transaction respectively complicating interpretation. Divergence is opposite EPS-surprise and price-reaction signs, not proof that EPS caused the movement. These cases are not presented as equally strong causal evidence.

C22 retains the reported-at-release 0.89 consensus and its original source limitation. It remains automatically eligible on comparable EPS bases; the available pre-release 0.90 would also be below actual EPS of 1.06, leaving the beat classification unchanged.

The shared `automatic_eps_eligible` validation gate requires earnings scope (`eps_and_price`) AND a verified comparable pair, non-null finite EPS values, matching accounting bases and currency/share/split units, and the correct event/quarter join. Pair-wide unit columns currently apply to both actual and consensus; any side-specific units must agree. `events.verified` concerns event metadata/date/timing only. `estimates.comparability_verified` concerns EPS comparability and cannot by itself override qualitative scope. Regression tests exercise C19/C25 with real numeric pairs, with scope-only changes, and with hypothetically comparable pairs still in qualitative scope; both stay excluded.

C12/C13 close-to-close returns include trading before their intraday announcements. C26 is broad trade-policy/market-sentiment context, not a direct semiconductor tariff. SOXX macro excess returns must use a broader SPY/QQQ benchmark or remain NULL; SOXX must not benchmark itself. Price, benchmark and metric implementation remains later-phase work.

The repository has no PostgreSQL table or loader to retrofit. The [explicit P2 staging/import contract](P2_IMPORT_CONTRACT.md) lists all 18 CSV fields and requires a named-column projection with eligibility metadata preserved. No direct positional copy into a seven-column table is permitted. This documentation makes the import requirement explicit without prematurely implementing P2.

Run `python3 scripts/validate_seed.py` and `python3 -m unittest discover -s tests -v`. The final hardening leaves `events_candidates.csv` untouched, including the previously authorized C20 correction. P1 remains complete and ready for P2; no commit or push is authorized.
