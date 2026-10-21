import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import duckdb

from homecost.db import initialize
from homecost.service import add_category, add_expense, add_expenses, add_payment_method, add_vendor, get_settings, set_setting


def _choice(prompt, values):
    for index, value in enumerate(values, 1):
        print(f"{index}. {value}")
    try:
        choice = int(input(prompt))
        return values[choice - 1]
    except (ValueError, IndexError):
        raise ValueError("choose one of the numbered options") from None


def _optional_date(prompt):
    value = input(prompt).strip()
    return date.fromisoformat(value) if value else None


def _optional_csv_date(value):
    value = (value or "").strip()
    return date.fromisoformat(value) if value else None


def _optional_csv_decimal(value):
    value = (value or "").strip()
    return Decimal(value) if value else None


def main(argv=None):
    parser = argparse.ArgumentParser(prog="homecost")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("add")
    import_command = commands.add_parser("import")
    import_command.add_argument("file")
    categories = commands.add_parser("categories")
    category_actions = categories.add_subparsers(dest="category_action")
    category_actions.add_parser("add")
    payment_methods = commands.add_parser("payment-methods")
    payment_method_actions = payment_methods.add_subparsers(dest="payment_method_action")
    payment_method_actions.add_parser("add")
    settings = commands.add_parser("settings")
    actions = settings.add_subparsers(dest="action")
    setting_set = actions.add_parser("set")
    setting_set.add_argument("key")
    setting_set.add_argument("value")
    args = parser.parse_args(argv)

    if args.command == "import":
        rows = []
        parse_errors = []
        try:
            with open(args.file, encoding="utf-8-sig", newline="") as source:
                reader = csv.DictReader(source)
                for line_number, row in enumerate(reader, 2):
                    if not any(value and value.strip() for value in row.values() if value is not None):
                        continue
                    try:
                        if not row.get("paid_date", "").strip():
                            raise ValueError("paid_date is required")
                        if not row.get("amount", "").strip():
                            raise ValueError("amount is required")
                        fields = {
                            "paid_date": date.fromisoformat(row["paid_date"].strip()),
                            "amount": Decimal(row["amount"].strip()),
                            "category": (row.get("category") or "").strip() or "unassigned",
                            "vendor": (row.get("vendor") or "").strip() or None,
                            "cost_month": _optional_csv_date(row.get("cost_month")),
                            "bill_date": _optional_csv_date(row.get("bill_date")),
                            "quantity": _optional_csv_decimal(row.get("quantity")),
                            "payment_method": (row.get("payment_method") or "").strip() or "unassigned",
                        }
                        rows.append((line_number, fields))
                    except (ValueError, InvalidOperation) as exc:
                        parse_errors.append(f"line {line_number}: {exc}")
        except OSError as exc:
            parser.exit(2, f"homecost: error: cannot read {args.file}: {exc}\n")
        home = Path.home() / ".homecost"
        home.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(home / "homecost.duckdb")) as db:
            ids, errors = add_expenses(db, rows, parse_errors)
        if errors:
            parser.exit(2, "homecost: import rejected; correct these rows and retry:\n" + "\n".join(errors) + "\n")
        print(f"Imported {len(ids)} expenses.")
        return 0

    if args.command == "payment-methods" and args.payment_method_action == "add":
        home = Path.home() / ".homecost"
        home.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(home / "homecost.duckdb")) as db:
            try:
                name = add_payment_method(db, input("Payment method name: "))
            except ValueError as exc:
                parser.exit(2, f"homecost: error: {exc}\n")
        print(f"Added payment method {name}.")
        return 0

    if args.command == "categories" and args.category_action == "add":
        home = Path.home() / ".homecost"
        home.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(home / "homecost.duckdb")) as db:
            try:
                name = input("Category name: ")
                unit = input("Unit (Enter for none): ").strip() or None
                answer = input("Monthly bill expected? [yes/no]: ").strip().lower()
                if answer not in {"yes", "no"}:
                    raise ValueError("answer yes or no")
                category = add_category(db, name, unit, answer == "yes")
            except ValueError as exc:
                parser.exit(2, f"homecost: error: {exc}\n")
        print(f"Added category {category}.")
        return 0

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

    if args.command == "add":
        home = Path.home() / ".homecost"
        db_path = home / "homecost.duckdb"
        home.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(db_path)) as db:
            initialize(db)
            try:
                paid_date = date.fromisoformat(input("Paid date (YYYY-MM-DD): ").strip())
                categories = db.execute(
                    "SELECT name, unit FROM categories WHERE name != 'unassigned' ORDER BY name"
                ).fetchall()
                category = _choice("Category number: ", [row[0] for row in categories])
                amount = Decimal(input("Amount: ").strip())
                methods = [row[0] for row in db.execute(
                    "SELECT name FROM payment_methods WHERE name != 'unassigned' ORDER BY name"
                ).fetchall()]
                payment_method = _choice("Payment method number: ", methods)

                vendors = [row[0] for row in db.execute("SELECT name FROM vendors ORDER BY name").fetchall()]
                for index, vendor in enumerate(vendors, 1):
                    print(f"{index}. {vendor}")
                print(f"{len(vendors) + 1}. Add a vendor")
                vendor_choice = input("Vendor number, or Enter to skip: ").strip()
                vendor = None
                if vendor_choice:
                    choice = int(vendor_choice)
                    if 1 <= choice <= len(vendors):
                        vendor = vendors[choice - 1]
                    elif choice == len(vendors) + 1:
                        vendor_name = input("Vendor name: ").strip()
                        vendor = add_vendor(db, vendor_name)
                    else:
                        raise ValueError("choose an existing vendor, add a vendor, or press Enter to skip")

                cost_month = _optional_date("Cost month (YYYY-MM-DD, Enter for paid month): ")
                bill_date = _optional_date("Bill date (YYYY-MM-DD, Enter to skip): ")
                unit = next(unit for name, unit in categories if name == category)
                quantity = Decimal(input(f"Quantity ({unit}): ").strip()) if unit else None
                expense_id = add_expense(
                    db,
                    paid_date=paid_date,
                    category=category,
                    amount=amount,
                    payment_method=payment_method,
                    vendor=vendor,
                    cost_month=cost_month,
                    bill_date=bill_date,
                    quantity=quantity,
                )
            except (ValueError, InvalidOperation) as exc:
                parser.exit(2, f"homecost: error: {exc}\n")
        print(f"Added expense {expense_id}.")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
