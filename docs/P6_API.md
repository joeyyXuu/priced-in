# P6 FastAPI integration

The local API reads reviewed events, estimates, prices and the persisted P5 metric snapshot from PostgreSQL. It never fetches Yahoo data or calculates financial metrics during a request. The connected frontend is served at `/`, with its JavaScript at `/assets/events.js`. Browser requests use the same origin as the API.

## Start and inspect

With P2–P5 initialized and PostgreSQL running:

```sh
python3 scripts/setup_api.py
```

Open http://127.0.0.1:8000/docs for interactive endpoint documentation and **Try it out**. The OpenAPI specification is at `/openapi.json`.

The setup command generates `API_DB_PASSWORD` in the ignored `.env` if absent, provisions `priced_in_api` with SELECT on the four required relations, builds the Python 3.13 container, and starts it. Existing CSVs, prices and metric values are preserved. The API connects to `db:5432` on Docker's internal network through psycopg; the public local address is `127.0.0.1:8000`.

```sh
docker compose exec -T api python -m unittest api.test_api -v
docker compose stop api
docker compose up -d api
```

Re-run setup after code changes to rebuild. Re-run `python3 scripts/metrics.py` after input changes to refresh the materialized metrics. The API does not automatically refresh stale metrics. Local development uses one database connection per request with a five-second connection/query timeout. Connection pooling, authentication, deployment and frontend CORS configuration can be added when their usage requires them; this service binds only to localhost.

## Endpoints

| GET path | Result |
|---|---|
| `/health` | Checks database access and metric relation availability |
| `/filters` | Available tickers, event types, years, patterns and scopes |
| `/events` | Paginated events with nested stored metrics |
| `/events/{candidate_id}` | Event metadata, stored metrics and sourced estimate record if present |
| `/events/{candidate_id}/prices` | Company and benchmark daily price/volume rows around the reaction session |

Examples:

```text
/events?ticker=NVDA&pattern=divergent
/events?event_type=macro
/events?year=2024&limit=5&offset=0
/events/C04
/events/C12/prices?before=60&after=5
```

The list supports `ticker`, `event_type`, `year`, `pattern`, `scope`, `limit` (1–100) and `offset`. Ordering is announcement date descending, then candidate ID; `total` is the number matching before pagination. `pattern` filters the calculated one-day pattern, not the research hypothesis.

The price window uses trading sessions: `before` is 1–120 preceding sessions, `after` is 1–20 sessions **including reaction day**. Defaults produce 65 dates and 130 rows for the event and benchmark. Bounds beyond stored history may return fewer dates; absent ticker prices remain null on available SPY session dates. SOXX events use SPY as benchmark; company events use SOXX.

Dates serialize as ISO strings and numbers as JSON numbers. Percentages are in percent units, excess returns in percentage points, and volume ratios in multiples. Null computed EPS values mean ineligible/unavailable, not zero. TSM detail responses retain provisional estimate values and FALSE comparability alongside null automatic EPS metrics. Research notes and source URLs are intentionally exposed for transparency.

Unknown event IDs return 404, invalid filter/window values 422, unsupported writes 405, and database errors a generic 503 without connection details. All input values are passed as SQL parameters. The database role has no table write privileges even if read-only transaction mode is disabled.

## Validation

Seven integration tests exercise real PostgreSQL through FastAPI's TestClient: health/OpenAPI, membership/filters/pagination, calculated values and TSM nulls, macro price windows, invalid inputs/unknown IDs/write routes, database write denial, and sanitized database failure responses. They use the restricted API login. No external market-data client is installed in the API image.
