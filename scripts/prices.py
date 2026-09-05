"""Fetch, validate and transactionally load daily Yahoo prices for the P1 sample."""
import argparse
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
import io
import json
import math
import statistics
from pathlib import Path
import time

from db import ROOT, psql, validate

OUT = ROOT / 'data/prices'
FIELDS = ['ticker', 'price_date', 'adjusted_close', 'volume', 'source', 'fetched_at']


def event_windows(events, sessions):
    windows = []
    for e in events:
        day = e['event_date']
        i = next(i for i, d in enumerate(sessions)
                 if d > day or (d == day and e['release_timing'] != 'amc'))
        if i < 60 or i + 4 >= len(sessions):
            raise ValueError('Insufficient calendar bounds')
        windows.append(dict(candidate_id=e['candidate_id'], ticker=e['ticker'],
                            benchmark='SPY' if e['ticker'] == 'SOXX' else 'SOXX',
                            reaction_date=sessions[i], previous_close_date=sessions[i-1],
                            fifth_session=sessions[i+4], required=sessions[i-60:i+5]))
    return windows


def validate_rows(rows, required):
    seen = set()
    for r in rows:
        key = (r['ticker'], r['price_date'])
        if key in seen:
            raise ValueError(f'Duplicate price: {key}')
        seen.add(key)
        p, v = float(r['adjusted_close']), float(r['volume'])
        if not math.isfinite(p) or p <= 0 or not math.isfinite(v) or v <= 0 or not v.is_integer():
            raise ValueError(f'Invalid price/volume: {key}')
    missing = required - seen
    if missing:
        raise ValueError(f'Missing {len(missing)} required sessions: {sorted(missing)[:10]}')


def load(rows):
    buffer = io.StringIO()
    csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator='\n').writerows(rows)
    sql = """BEGIN;
SELECT pg_advisory_xact_lock(731903);
CREATE TEMP TABLE stage_prices (LIKE prices INCLUDING DEFAULTS INCLUDING CONSTRAINTS) ON COMMIT DROP;
COPY stage_prices (ticker,price_date,adjusted_close,volume,source,fetched_at) FROM STDIN WITH (FORMAT csv);
""" + buffer.getvalue() + "\\.\n" + """
INSERT INTO prices (ticker,price_date,adjusted_close,volume,source,fetched_at)
SELECT ticker,price_date,adjusted_close,volume,source,fetched_at FROM stage_prices
ON CONFLICT (ticker,price_date) DO UPDATE SET
adjusted_close=EXCLUDED.adjusted_close,volume=EXCLUDED.volume,
source=EXCLUDED.source,fetched_at=EXCLUDED.fetched_at;
COMMIT;
"""
    psql(input=sql, text=True, capture_output=True)


def main():
    import exchange_calendars as xcals
    import yfinance as yf
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Download new snapshots instead of reusing local cache')
    args = parser.parse_args()
    validate()
    psql('-f', '/sql/03_verify_seed.sql', capture_output=True, text=True)
    events = list(csv.DictReader((ROOT / 'data/events.csv').open()))
    start = date.fromisoformat(min(e['event_date'] for e in events)) - timedelta(days=150)
    end = date.fromisoformat(max(e['event_date'] for e in events)) + timedelta(days=30)
    cal = xcals.get_calendar('XNYS', start=start, end=end)
    # exchange-calendars 4.5.6 predates the Carter closure.
    # https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2024-87
    sessions = [d.date().isoformat() for d in cal.sessions
                if d.date() < end and d.date().isoformat() != '2025-01-09']
    windows = event_windows(events, sessions)
    required = {(t, d) for w in windows for t in (w['ticker'], w['benchmark']) for d in w['required']}
    OUT.mkdir(exist_ok=True)
    yf.set_tz_cache_location(str(OUT / '.cache'))
    rows, manifest, quality = [], [], []
    for ticker in sorted({t for t, _ in required}):
        path = OUT / f'{ticker}.csv'
        meta_path = OUT / f'{ticker}.json'
        if args.refresh or not path.exists() or not meta_path.exists():
            print(f'Fetching {ticker}: {start} through {end} (exclusive)', flush=True)
            for attempt in range(3):
                try:
                    frame = yf.Ticker(ticker).history(start=str(start), end=str(end), interval='1d',
                        auto_adjust=False, back_adjust=False, actions=True, repair=False,
                        keepna=True, raise_errors=True, timeout=30)
                    if frame.empty:
                        raise ValueError(f'Empty response for {ticker}')
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(2 ** attempt)
            frame.to_csv(path, index_label='Date')
            meta_path.write_text(json.dumps(dict(ticker=ticker, start=str(start), end_exclusive=str(end),
                fetched_at=datetime.now(timezone.utc).isoformat(), yfinance=yf.__version__,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest()), indent=2) + '\n')
        meta = json.loads(meta_path.read_text())
        if meta['sha256'] != hashlib.sha256(path.read_bytes()).hexdigest() or meta['start'] != str(start) or meta['end_exclusive'] != str(end):
            raise ValueError(f'Cache mismatch for {ticker}; use --refresh')
        manifest.append(meta)
        raw = list(csv.DictReader(path.open()))
        for i, r in enumerate(raw):
            if float(r.get('Stock Splits', 0)):
                quality.append(dict(ticker=ticker, date=r['Date'][:10], kind='split', value=r['Stock Splits']))
            if i >= 60:
                median = statistics.median(float(v['Volume']) for v in raw[i-60:i])
                if float(r['Volume']) > 10 * median:
                    quality.append(dict(ticker=ticker, date=r['Date'][:10], kind='volume_above_10x_prior_median', value=r['Volume']))
        for r in raw:
            day = r['Date'][:10]
            if day not in sessions:
                raise ValueError(f'Unexpected session {ticker} {day}')
            rows.append(dict(ticker=ticker, price_date=day, adjusted_close=r['Adj Close'],
                             volume=r['Volume'], source='yahoo_finance/yfinance:' + meta['yfinance'],
                             fetched_at=meta['fetched_at']))
    # Require every session across the entire requested range, not just event windows.
    validate_rows(rows, {(t, d) for t in {t for t, _ in required} for d in sessions})
    load(rows)
    actual = psql('-qAt', '-c', 'SELECT ticker,price_date,adjusted_close,volume,source,fetched_at FROM prices ORDER BY ticker,price_date',
                  '--csv', capture_output=True, text=True).stdout
    db_rows = list(csv.DictReader(io.StringIO(actual), fieldnames=FIELDS))
    validate_rows(db_rows, required)
    observed = {(r['ticker'], r['price_date']): r for r in db_rows}
    for r in rows:
        stored = observed[(r['ticker'], r['price_date'])]
        if float(stored['adjusted_close']) != float(r['adjusted_close']) or int(stored['volume']) != int(r['volume']):
            raise ValueError('Database round-trip mismatch')
    (ROOT / 'data/p3_quality.json').write_text(json.dumps(quality, indent=2) + '\n')
    report = ROOT / 'data/p3_coverage.csv'
    with report.open('w') as f:
        writer = csv.DictWriter(f, fieldnames=['candidate_id','ticker','benchmark','reaction_date','previous_close_date','fifth_session','prior_sessions','status'])
        writer.writeheader()
        for w in windows:
            writer.writerow({**{k:v for k,v in w.items() if k != 'required'}, 'prior_sessions':60, 'status':'PASS'})
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'PASS: {len(rows)} prices, {len(manifest)} tickers, {len(windows)} complete event windows. Report: {report}')


if __name__ == '__main__':
    main()
