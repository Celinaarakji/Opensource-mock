"""Run the server: `python -m gamejam` (add --seed for demo data)."""

import argparse
import logging

from gamejam import config, db
from gamejam.app import create_router
from gamejam.seed import seed
from gamejam.web import serve


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the Game Jam API")
    parser.add_argument("--db", default=config.DB_PATH, help="SQLite file (default: gamejam.db)")
    parser.add_argument("--host", default=config.HOST)
    parser.add_argument("--port", type=int, default=config.PORT)
    parser.add_argument("--seed", action="store_true", help="Reset the database with demo data")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    conn = db.get_connection(args.db)
    if args.seed:
        tokens = seed(conn)
        print("\nDemo data loaded. Use these tokens in the Authorization header:")
        for username, token in tokens.items():
            print(f"  {username:<14} Bearer {token}")
        print()
    else:
        db.init_db(conn)

    serve(create_router(), conn, args.host, args.port)


if __name__ == "__main__":
    main()
