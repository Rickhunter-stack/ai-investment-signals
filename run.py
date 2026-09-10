import argparse
from datetime import datetime, timezone
from src.db import connect
from src.market import update_market


def init_db():
    conn = connect()
    conn.close()
    print('Database initialized')


def market():
    n = update_market()
    print(f'Market rows updated: {n}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--step', choices=['init','market','all'], default='all')
    args = parser.parse_args()
    if args.step in ('init','all'):
        init_db()
    if args.step in ('market','all'):
        market()

if __name__ == '__main__':
    main()
