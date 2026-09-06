"""Provision a SELECT-only database login and start the local API."""
import secrets
from db import ROOT, compose, psql


def main():
    env = ROOT / '.env'
    values = dict(line.split('=',1) for line in env.read_text().splitlines() if '=' in line and not line.startswith('#'))
    password=values.get('API_DB_PASSWORD')
    if not password:
        password=secrets.token_hex(32)
        with env.open('a') as f:
            f.write('\nAPI_DB_PASSWORD='+password+'\n')
    # Pass the secret through stdin, never a shell command or command-line argument.
    escaped=password.replace("'", "''")
    sql="""BEGIN;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='priced_in_api') THEN
 CREATE ROLE priced_in_api LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
 END IF;
END $$;
ALTER ROLE priced_in_api PASSWORD '"""+escaped+"""';
ALTER ROLE priced_in_api SET default_transaction_read_only=on;
GRANT CONNECT ON DATABASE priced_in TO priced_in_api;
GRANT USAGE ON SCHEMA public TO priced_in_api;
GRANT SELECT ON events,estimates,prices,event_metrics TO priced_in_api;
COMMIT;
"""
    psql(input=sql,text=True,capture_output=True)
    compose('up','-d','--build','--wait','--wait-timeout','90','api')
    print('API started at http://127.0.0.1:8000; interactive documentation at /docs')


if __name__=='__main__':
    main()
