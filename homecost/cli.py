import argparse
from pathlib import Path

import duckdb

from homecost.service import get_settings, set_setting


def main(argv=None):
    parser = argparse.ArgumentParser(prog="homecost")
    commands = parser.add_subparsers(dest="command")
    settings = commands.add_parser("settings")
    actions = settings.add_subparsers(dest="action")
    setting_set = actions.add_parser("set")
    setting_set.add_argument("key")
    setting_set.add_argument("value")
    args = parser.parse_args(argv)
    if args.command == "settings":
        home = Path.home() / ".homecost"
        db_path = home / "homecost.duckdb"
        home.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(db_path)) as db:
            if args.action == "set":
                confirm = True
                if args.key == "timezone":
                    confirm = input("Changing the time zone does not rewrite stored dates. Continue? [y/N] ").strip().lower() == "y"
                try:
                    set_setting(db, args.key, args.value, confirm_timezone=confirm)
                except ValueError as exc:
                    parser.exit(2, f"homecost: error: {exc}\n")
            else:
                for key, value in sorted(get_settings(db).items()):
                    print(f"{key}: {value}")
                print(f"database: {db_path}")
                print(f"backups: {home / 'backups'}")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
