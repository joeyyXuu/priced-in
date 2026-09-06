"""Read-only HTTP access to reviewed events and persisted SQL metrics."""
import os
from typing import Literal

import psycopg
from psycopg.rows import dict_row
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(title='Priced In API', version='1.0.0', description='Retrospective event study. Percentages and classifications are calculated in PostgreSQL; null means unavailable or ineligible.')
Ticker = Literal['NVDA','AMD','INTC','TSM','MU','AVGO','SOXX']
EventType = Literal['earnings','guidance','macro','product','acquisition']


def connection():
    with psycopg.connect(host=os.environ.get('DB_HOST','db'), dbname='priced_in',
                         user='priced_in_api', password=os.environ['API_DB_PASSWORD'],
                         connect_timeout=5, row_factory=dict_row,
                         options='-c default_transaction_read_only=on -c statement_timeout=5000') as conn:
        yield conn


@app.exception_handler(psycopg.Error)
def database_error(request, exc):
    return JSONResponse(status_code=503, content={'detail':'Database unavailable or metric setup incomplete'})


@app.get('/health')
def health(conn=Depends(connection)):
    conn.execute('SELECT candidate_id FROM event_metrics LIMIT 1').fetchone()
    return {'status':'ok'}


@app.get('/filters')
def filters(conn=Depends(connection)):
    rows=conn.execute('SELECT DISTINCT ticker,event_type,extract(year FROM event_date)::int AS year FROM events').fetchall()
    return {'tickers':sorted({r['ticker'] for r in rows}),
            'event_types':sorted({r['event_type'] for r in rows}),
            'years':sorted({r['year'] for r in rows}),
            'patterns':['aligned','divergent'], 'scopes':['eps_and_price','qualitative','macro_price']}


BASE = 'SELECT e.*, to_jsonb(m) AS metrics FROM events e JOIN event_metrics m USING(candidate_id)'


@app.get('/events')
def events(ticker: Ticker | None=None, event_type: EventType | None=None,
           year: int | None=Query(None,ge=2019,le=2025),
           pattern: Literal['aligned','divergent'] | None=None,
           scope: Literal['eps_and_price','qualitative','macro_price'] | None=None,
           limit: int=Query(20,ge=1,le=100), offset: int=Query(0,ge=0), conn=Depends(connection)):
    clauses,params=[],[]
    for field,value in [('e.ticker',ticker),('e.event_type',event_type),
                        ('extract(year FROM e.event_date)',year),('m.calculated_pattern',pattern),('e.analysis_scope',scope)]:
        if value is not None:
            clauses.append(field+' = %s')
            params.append(value)
    where=' WHERE '+' AND '.join(clauses) if clauses else ''
    total=conn.execute('SELECT count(*) AS n FROM events e JOIN event_metrics m USING(candidate_id)'+where,params).fetchone()['n']
    items=conn.execute(BASE+where+' ORDER BY e.event_date DESC,e.candidate_id LIMIT %s OFFSET %s',params+[limit,offset]).fetchall()
    return {'total':total,'limit':limit,'offset':offset,'items':items}


def get_event(candidate_id,conn):
    row=conn.execute(BASE+' WHERE e.candidate_id=%s',(candidate_id,)).fetchone()
    if row is None:
        raise HTTPException(404,'Event not found')
    return row


@app.get('/events/{candidate_id}')
def detail(candidate_id: str,conn=Depends(connection)):
    row=get_event(candidate_id,conn)
    row['estimate']=conn.execute('SELECT * FROM estimates WHERE candidate_id=%s',(candidate_id,)).fetchone()
    return row


@app.get('/events/{candidate_id}/prices')
def price_window(candidate_id: str, before: int=Query(60,ge=1,le=120),
                 after: int=Query(5,ge=1,le=20),conn=Depends(connection)):
    event=get_event(candidate_id,conn)
    m=event['metrics']
    rows=conn.execute('''WITH sessions AS (
      (SELECT price_date FROM prices WHERE ticker='SPY' AND price_date<%s ORDER BY price_date DESC LIMIT %s)
      UNION ALL
      (SELECT price_date FROM prices WHERE ticker='SPY' AND price_date>=%s ORDER BY price_date LIMIT %s)
    ) SELECT s.price_date,t.ticker,p.adjusted_close,p.volume,p.source,p.fetched_at
      FROM sessions s CROSS JOIN (VALUES (%s::text),(%s::text)) t(ticker)
      LEFT JOIN prices p ON p.price_date=s.price_date AND p.ticker=t.ticker
      ORDER BY s.price_date,t.ticker''',
      (m['reaction_date'],before,m['reaction_date'],after,event['ticker'],m['benchmark'])).fetchall()
    return {'candidate_id':candidate_id,'reaction_date':m['reaction_date'],
            'ticker':event['ticker'],'benchmark':m['benchmark'],
            'before':before,'after_including_reaction':after,'items':rows}


WEB = Path(__file__).resolve().parents[1] / "web"
app.mount("/assets", StaticFiles(directory=WEB), name="assets")


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(WEB / "events-draft.html")
