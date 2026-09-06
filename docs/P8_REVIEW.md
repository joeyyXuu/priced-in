# P8 methodology and documentation acceptance

P8 is complete for the current local application. Public deployment remains P9. The documentation records the implemented HTML/CSS/JavaScript frontend; no React migration is claimed.

## Delivered

- `/methodology`, served from `web/methodology.html`, covers selection, timing, adjusted closes, volume, EPS accounting and units, benchmarks, formulas, nulls, worked examples and limitations. Event navigation and the inline explanation link to it; it links back to the event list.
- `docs/OPERATIONS.md` consolidates prerequisites, the first-run pipeline order, separate price/API environments, refresh and restart commands, validation and troubleshooting.
- README language now describes implemented calculations and services. The previously ambiguous volume wording explicitly excludes the reaction day, with announcement-day trading included for after-close events. The benchmark is explicitly SPY for SOXX macro cases.
- Architecture and frontend notes link to the current workflow. Phase-specific evidence reviews remain available as audit history rather than being rewritten as fresh source verification.

## Methodology boundaries retained

The sample remains 20 selected events with 11 automatically eligible EPS pairs. TSM C19/C25 remain qualitative and C20 stays excluded. Research hypotheses remain distinct from calculated patterns. No new sources, prices, EPS values, event membership or SQL formulas were introduced by P8.

The page explains zero-consensus handling separately from the sign test, adjusted-price versus announcement-date EPS units, documentary consensus snapshot limits, SPY/SOXX benchmark selection, and the distinction between mechanical divergence and causal or statistical claims. C16/C22 confounders and C19's differing research/closing windows remain explicit.

## Verification

The local service was rebuilt and reached healthy status. Real Chrome checks exercised Events → Methodology → Events, all six methodology sections, and a 390-pixel viewport with no page overflow. Existing event loading, filters, details, null EPS, benchmark and failure/retry checks also passed without browser errors.

The documented validation commands passed: 15 offline tests, seven database tests, four SQL metric tests and seven API tests (33 total), plus the read-only EPS/database parity audit. The first-run commands were checked against the implementation; a new empty database was not provisioned and external price data was not re-downloaded for this documentation phase. Existing dependency warnings are disclosed in the operations guide.

No public deployment, commit or push was performed. P9 can be planned separately with hosting and operational requirements made concrete before deployment.
