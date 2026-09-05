"""Local PostgreSQL lifecycle and seed checks, using Docker's bundled psql."""

import argparse
import os
from pathlib import Path
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(args, **kwargs):
    return subprocess.run(args, cwd=ROOT, check=True, **kwargs)


def compose(*args, **kwargs):
    return run(['docker', 'compose', *args], **kwargs)


def psql(*args, **kwargs):
    return compose('exec', '-T', 'db', 'psql', '-X', '-v', 'ON_ERROR_STOP=1',
                   '-U', 'priced_in', '-d', 'priced_in', *args, **kwargs)


def validate():
    run([sys.executable, '-B', str(ROOT / 'scripts/validate_seed.py')])


def ensure_env():
    try:
        fd = os.open(ROOT / '.env', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return
    with os.fdopen(fd, 'w') as env:
        env.write(f'POSTGRES_PASSWORD={secrets.token_hex(32)}\nPOSTGRES_PORT=5433\n')
    print('Created ignored .env with a generated local password; existing files are never overwritten.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['setup', 'load', 'check', 'test', 'stop'])
    command = parser.parse_args().command
    if command == 'setup':
        validate()
        ensure_env()
        compose('up', '-d', '--wait', '--wait-timeout', '90', 'db')
        psql('-f', '/sql/02_load_seed.sql')
    elif command == 'load':
        validate()
        psql('-f', '/sql/02_load_seed.sql')
    elif command == 'check':
        psql('-f', '/sql/03_verify_seed.sql')
    elif command == 'test':
        validate()
        run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
        run([sys.executable, '-B', str(ROOT / 'scripts/test_database.py')])
    else:
        compose('stop', 'db')


if __name__ == '__main__':
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f'Database command failed: {exc}', file=sys.stderr)
        sys.exit(1)
