# Local setup and maintenance

This is the current P1–P8 local workflow. Public deployment remains P9. The interface uses HTML, CSS and JavaScript, served by FastAPI; the originally proposed React migration was not performed.

## Requirements and first setup

Use Docker with Compose and a running Docker engine, Python 3 for the maintenance commands, and ports 5433 and 8000 available on localhost. Price collection was tested in a Python 3.9 virtual environment with `requirements-prices.txt`. The API builds its own Python 3.13 environment from `api/requirements.txt`. The original root `requirements.txt` is not the installation recipe for these two separate environments.

Run from the repository root in this order:

```sh
# 1. Validate and import approved events/estimates; start PostgreSQL.
python3 scripts/db.py setup

# 2. Create the price environment (once) and import historical prices.
python3 -m venv .venv
.venv/bin/pip install -r requirements-prices.txt
.venv/bin/python scripts/prices.py

# 3. Audit EPS parity, calculate SQL metrics, export audit results.
python3 scripts/validate_estimates.py
python3 scripts/metrics.py

# 4. Provision the SELECT-only API role and build/start the app.
python3 scripts/setup_api.py
```

Open http://127.0.0.1:8000/ for events, `/methodology` for the study explanation, and `/docs` for interactive API documentation. Opening the HTML from disk does not connect it to the API.

Setup creates ignored `.env` credentials without printing them. The database setup preserves an existing `.env`; API setup adds its generated password if absent. PostgreSQL tables persist in the `priced-in_postgres_data` Docker volume. Local CSVs and SQL files are read-only mounts inside that container. Changing a CSV does not automatically change a table, and changing a password setting does not automatically rotate the initialized database administrator password.

The API login reads only events, estimates, prices and the materialized metric snapshot. API requests do not fetch market data or refresh calculations. Python maintenance commands use Docker's `psql`; FastAPI uses psycopg directly. See [architecture](ARCHITECTURE_OVERVIEW.md).

## Routine changes

| Change | Follow-up |
|---|---|
| Restart existing app | `docker compose up -d --wait db api` |
| Stop app and database, retain stored data | `docker compose stop api db` |
| Edit frontend/API code | `python3 scripts/setup_api.py` rebuilds the local image |
| Approved event/estimate input correction | Run `python3 scripts/db.py load`, recheck price coverage, then refresh metrics and validate |
| Reuse downloaded price snapshot | `.venv/bin/python scripts/prices.py` |
| Fetch revised provider data | `.venv/bin/python scripts/prices.py --refresh`, then `python3 scripts/metrics.py` and review reconciliation |
| Change SQL calculation logic | Run `python3 scripts/metrics.py`, then SQL tests and reconciliation review |

The price importer checks hashes and bounds before reusing cached files. Refresh explicitly replaces local snapshots; retain copies first if you need to compare provider revisions. The metric materialized view does not refresh automatically after input changes. Shape changes to tables or views require explicit migrations; the current repeatable setup is not a general migration framework.

The seed loader enforces the approved sample. Expanding or replacing sample membership is a methodological change requiring coordinated data, acceptance-check and documentation updates.

## Validation commands

```sh
# Offline CSV consistency and unit tests:
python3 scripts/validate_seed.py
python3 -B -m unittest discover -s tests -v

# Existing 15 offline tests plus 7 PostgreSQL integration tests:
python3 scripts/db.py test

# Read-only EPS/database parity and 4 live SQL calculation tests:
python3 scripts/validate_estimates.py
python3 scripts/test_metrics.py

# 7 API tests against the real database:
docker compose exec -T api python -m unittest api.test_api -v

# HTTP readiness:
curl --fail http://127.0.0.1:8000/health
```

`db.py test` already includes the offline suite; the separate offline command is useful without Docker. Run live fixture tests against the local development database without concurrent writers. They roll back temporary mutations. The API test verifies that writes are denied even when its transaction read-only setting is disabled.

Review `data/p3_coverage.csv`, `data/p4_estimate_review.csv`, `data/p5_metrics.csv`, and `data/p5_reconciliation.csv` after changing inputs. A source/SQL discrepancy must trigger review; never alter a window or input just to preserve the eight-case count.

Browser acceptance: load all events; exercise type/ticker/year/pattern filters; open a TSM detail and confirm blank computed EPS with unverified research values; open a macro detail and confirm SPY; check an empty filter combination and service-error Retry; follow Methodology and return to Events; inspect mobile layout. Browser tooling is optional and was used temporarily outside the repository.

## Troubleshooting

- **Docker unavailable:** start Docker, then retry setup. A virtual environment does not start the database.
- **Port conflict:** set `POSTGRES_PORT` in `.env` before database startup; the API's localhost port is configured in Compose.
- **API 503/unhealthy:** confirm PostgreSQL is running and P5 has populated `event_metrics`. Run the documented stages in order, then API setup to provision its role.
- **Old metrics after an edit:** reimport the appropriate input and run `scripts/metrics.py`; a browser reload alone cannot refresh a materialized view.
- **No matching events:** clear filters. This is a valid empty result, not an API error.
- **Price cache mismatch or calendar gap:** investigate the reported dates/hash before refreshing. Do not forward-fill a missing price or skip a session to obtain a return.

The price environment's system LibreSSL and the API test client's httpx compatibility currently emit documented warnings; the verified commands still pass. Dependency upgrades should rerun price/calendar, SQL and API checks. See [P3 review](P3_REVIEW.md) and [API contract](P6_API.md).
