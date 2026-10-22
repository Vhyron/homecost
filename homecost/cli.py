import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import duckdb

from homecost.db import initialize
from homecost.service import ManagedTransaction, add_category, add_expense, add_expenses, add_payment_method, add_vendor, archive_managed_value, bill_status, category_totals, create_backup, delete_expense, edit_expense, find_duplicate, get_settings, grocery_trip_summary, is_current_period, list_expenses, list_managed_values, metered_summary, month_detail, period_total, rename_managed_value, restore_backup, same_expense, set_setting, today_in_timezone, validate_expenses


def _choice(prompt, values, allow_empty=False):
    """Show numbered choices starting at 1 and re-prompt until the answer is valid."""
    while True:
        for index, value in enumerate(values, 1):
            print(f"{index}. {value}")
        raw = input(prompt).strip()
        if allow_empty and not raw:
            return None
        try:
            choice = int(raw)
        except ValueError:
            print("Enter a number from the list.")
            continue
        if 1 <= choice <= len(values):
            return choice - 1
        print(f"Enter a number between 1 and {len(values)}.")


def _prompt_date(prompt, *, allow_empty=False, error="Enter the date as YYYY-MM-DD."):
    while True:
        raw = input(prompt).strip()
        if not raw:
            if allow_empty:
                return None
            print("This field is required.")
            continue
        try:
            return date.fromisoformat(raw)
        except ValueError:
            print(error)


def _optional_month(prompt):
    while True:
        value = input(prompt).strip()
        if not value:
            return None
        year, separator, month = value.partition("-")
        if (
            separator == "-"
            and len(year) == 4
            and len(month) == 2
            and year.isdigit()
            and month.isdigit()
            and 1 <= int(month) <= 12
        ):
            return date(int(year), int(month), 1)
        print("Enter the cost month as YYYY-MM (for example, 2025-09), or press Enter to use the paid month.")


def _prompt_amount():
    while True:
        raw = input("Amount: ").strip()
        if not raw:
            print("This field is required.")
            continue
        try:
            value = Decimal(raw)
        except InvalidOperation:
            print("Enter a positive amount with at most two decimal places (for example, 123.45).")
            continue
        if not value.is_finite() or value <= 0 or value != value.quantize(Decimal("0.01")):
            print("Enter a positive amount with at most two decimal places (for example, 123.45).")
            continue
        return value


def _prompt_quantity(unit):
    while True:
        raw = input(f"Quantity ({unit}): ").strip()
        if not raw:
            print("This field is required.")
            continue
        try:
            value = Decimal(raw)
        except InvalidOperation:
            print("Enter a positive quantity with at most three decimal places.")
            continue
        if not value.is_finite() or value <= 0 or value != value.quantize(Decimal("0.001")):
            print("Enter a positive quantity with at most three decimal places.")
            continue
        return value


def _add_payment_method_flow(db):
    return add_payment_method(db, input("Payment method name: "))


def _add_category_flow(db):
    name = input("Category name: ")
    unit = input("Unit (Enter for none): ").strip() or None
    answer = input("Monthly bill expected? [yes/no]: ").strip().lower()
    if answer not in {"yes", "no"}:
        raise ValueError("answer yes or no")
    return add_category(db, name, unit, answer == "yes")


def _optional_csv_date(value):
    value = (value or "").strip()
    return date.fromisoformat(value) if value else None


def previous_month(period):
    year, month = map(int, period.split("-"))
    return f"{year - 1}-12" if month == 1 else f"{year}-{month - 1:02d}"


def _optional_csv_decimal(value):
    value = (value or "").strip()
    return Decimal(value) if value else None


def main(argv=None):
    parser = argparse.ArgumentParser(prog="homecost")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("add")
    import_command = commands.add_parser("import")
    import_command.add_argument("file")
    list_command = commands.add_parser("list")
    list_command.add_argument("--category")
    list_command.add_argument("--payment-method")
    edit_command = commands.add_parser("edit")
    edit_command.add_argument("expense_id", type=int)
    delete_command = commands.add_parser("delete")
    delete_command.add_argument("expense_id", type=int)
    categories = commands.add_parser("categories")
    category_actions = categories.add_subparsers(dest="category_action")
    category_actions.add_parser("add")
    category_actions.add_parser("list")
    category_rename = category_actions.add_parser("rename")
    category_rename.add_argument("old_name")
    category_rename.add_argument("new_name")
    category_remove = category_actions.add_parser("remove")
    category_remove.add_argument("name")
    vendors = commands.add_parser("vendors")
    vendor_actions = vendors.add_subparsers(dest="vendor_action")
    vendor_actions.add_parser("list")
    vendor_actions.add_parser("add")
    vendor_rename = vendor_actions.add_parser("rename")
    vendor_rename.add_argument("old_name")
    vendor_rename.add_argument("new_name")
    vendor_remove = vendor_actions.add_parser("remove")
    vendor_remove.add_argument("name")
    payment_methods = commands.add_parser("payment-methods")
    payment_method_actions = payment_methods.add_subparsers(dest="payment_method_action")
    payment_method_actions.add_parser("add")
    payment_method_actions.add_parser("list")
    method_rename = payment_method_actions.add_parser("rename")
    method_rename.add_argument("old_name")
    method_rename.add_argument("new_name")
    method_remove = payment_method_actions.add_parser("remove")
    method_remove.add_argument("name")
    settings = commands.add_parser("settings")
    actions = settings.add_subparsers(dest="action")
    setting_set = actions.add_parser("set")
    setting_set.add_argument("key")
    setting_set.add_argument("value")
    report = commands.add_parser("report")
    report.add_argument("period")
    report.add_argument("--basis", choices=("cost_month", "paid_date"), default="cost_month")
    commands.add_parser("backup")
    restore = commands.add_parser("restore")
    restore.add_argument("backup")
    restore.add_argument("--to", dest="target", required=True)
    args = parser.parse_args(argv)

    if args.command == "restore":
        try:
            restore_backup(args.backup, args.target)
        except ValueError as exc:
            parser.exit(2, f"homecost: error: {exc}\\n")
        print(f"Restored {args.backup} to {args.target}.")
        return 0

    if args.command == "backup":
        home = Path.home() / ".homecost"
        home.mkdir(parents=True, exist_ok=True)
        db_path = home / "homecost.duckdb"
        with duckdb.connect(str(db_path)) as db:
            retention = int(get_settings(db)["backup-retention"])
            path = create_backup(db, db_path, home / "backups", retention=retention)
        print(f"Backup created: {path}")
        return 0

    if args.command == "report":
        home = Path.home() / ".homecost"
        home.mkdir(parents=True, exist_ok=True)
        try:
            with duckdb.connect(str(home / "homecost.duckdb")) as db:
                label = " (to date)" if is_current_period(db, args.period) else ""
                print(f"Report {args.period} ({args.basis}){label}")
                totals = category_totals(db, args.period, basis=args.basis)
                if not totals:
                    print("No expenses recorded for this period.")
                for category, total in totals:
                    print(f"{category}: {total}")
                print(f"Total: {period_total(db, args.period, basis=args.basis)}")
                print("Month detail:")
                for month, category, total in month_detail(db, args.period, basis=args.basis):
                    print(f"{month:%Y-%m} {category}: {total}")
                groceries = grocery_trip_summary(db, args.period, basis=args.basis)
                if groceries:
                    print(f"groceries trips: {groceries[0]}; average: {groceries[1]}")
                if args.period.count("-") == 1 and "-Q" not in args.period:
                    for category, total, quantity, unit_cost, usage_change, cost_change in metered_summary(db, args.period, basis=args.basis):
                        if usage_change is None:
                            previous = previous_month(args.period)
                            print(f"{category} metered: {total} over {quantity} ({unit_cost}/unit). Comparison unavailable: no usage was recorded for {previous}.")
                        else:
                            print(f"{category} metered: {total} over {quantity} ({unit_cost}/unit). Usage change: {usage_change:+}; unit-cost change: {cost_change:+}.")
                for month, category, status in bill_status(db, args.period):
                    print(f"{month:%Y-%m} {category} bill: {status}")
        except ValueError as exc:
            parser.exit(2, f"homecost: error: {exc}\n")
        return 0

    if args.command == "list":
        home = Path.home() / ".homecost"
        home.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(home / "homecost.duckdb")) as db:
            rows = list_expenses(db, category=args.category, payment_method=args.payment_method)
            headers = ("ID", "paid date", "category", "amount", "payment method", "vendor", "cost month")
            cells = [
                (str(row[0]), str(row[1]), row[2], str(row[3]), row[7], row[4] or "", str(row[5]))
                for row in rows
            ]
            widths = [
                max([len(header)] + [len(cell[i]) for cell in cells]) if cells else len(header)
                for i, header in enumerate(headers)
            ]
            print("  ".join(header.ljust(width) for header, width in zip(headers, widths)))
            for cell in cells:
                print("  ".join(value.ljust(width) for value, width in zip(cell, widths)))
        return 0

    list_kind = None
    if args.command == "categories" and args.category_action == "list":
        list_kind = "category"
    elif args.command == "vendors" and args.vendor_action == "list":
        list_kind = "vendor"
    elif args.command == "payment-methods" and args.payment_method_action == "list":
        list_kind = "payment_method"
    if list_kind:
        home = Path.home() / ".homecost"
        home.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(home / "homecost.duckdb")) as db:
            for name, status in list_managed_values(db, list_kind):
                print(f"{name} ({status})")
        return 0

    if args.command == "vendors" and args.vendor_action == "add":
        home = Path.home() / ".homecost"
        home.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(home / "homecost.duckdb")) as db:
            try:
                name = add_vendor(db, input("Vendor name: "))
            except ValueError as exc:
                parser.exit(2, f"homecost: error: {exc}\n")
        print(f"Added vendor {name}.")
        return 0

    rename_kind = None
    if args.command == "categories" and args.category_action == "rename":
        rename_kind = "category"
    elif args.command == "vendors" and args.vendor_action == "rename":
        rename_kind = "vendor"
    elif args.command == "payment-methods" and args.payment_method_action == "rename":
        rename_kind = "payment_method"
    remove_kind = None
    if args.command == "categories" and args.category_action == "remove":
        remove_kind = "category"
    elif args.command == "vendors" and args.vendor_action == "remove":
        remove_kind = "vendor"
    elif args.command == "payment-methods" and args.payment_method_action == "remove":
        remove_kind = "payment_method"
    if remove_kind:
        if input(f"Archive {remove_kind} {args.name!r}? [yes/no]: ").strip().lower() != "yes":
            print("Removal canceled.")
            return 0
        home = Path.home() / ".homecost"
        home.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(home / "homecost.duckdb")) as db:
            try:
                count = archive_managed_value(db, remove_kind, args.name)
            except ValueError as exc:
                parser.exit(2, f"homecost: error: {exc}\n")
        print(f"Archived {remove_kind} {args.name!r}; {count} expenses retain it.")
        return 0

    if rename_kind:
        if input(f"Rename {rename_kind} {args.old_name!r} to {args.new_name!r}? [yes/no]: ").strip().lower() != "yes":
            print("Rename canceled.")
            return 0
        home = Path.home() / ".homecost"
        home.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(home / "homecost.duckdb")) as db:
            try:
                count = rename_managed_value(db, rename_kind, args.old_name, args.new_name)
            except ValueError as exc:
                parser.exit(2, f"homecost: error: {exc}\n")
        print(f"Renamed {rename_kind} {args.old_name!r} to {args.new_name!r}; updated {count} expenses.")
        return 0

    if args.command == "delete":
        confirmation = input(f"Permanently delete expense {args.expense_id}? [yes/no]: ").strip().lower()
        if confirmation != "yes":
            print("Delete canceled.")
            return 0
        home = Path.home() / ".homecost"
        home.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(home / "homecost.duckdb")) as db:
            try:
                delete_expense(db, args.expense_id)
            except ValueError as exc:
                parser.exit(2, f"homecost: error: {exc}\n")
        print(f"Deleted expense {args.expense_id}.")
        return 0

    if args.command == "edit":
        home = Path.home() / ".homecost"
        home.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(home / "homecost.duckdb")) as db:
            initialize(db)
            row = db.execute(
                """SELECT paid_date, category, amount, payment_method, vendor, cost_month, bill_date, quantity
                   FROM expenses WHERE id=?""",
                [args.expense_id],
            ).fetchone()
            if row is None:
                parser.exit(2, f"homecost: error: expense {args.expense_id} does not exist\n")
            fields = dict(zip(
                ("paid_date", "category", "amount", "payment_method", "vendor", "cost_month", "bill_date", "quantity"),
                row,
            ))
            changes = {}
            try:
                for key in ("paid_date", "category", "amount", "payment_method"):
                    raw = input(f"{key.replace('_', ' ')} [{fields[key]}]: ").strip()
                    if raw:
                        changes[key] = date.fromisoformat(raw) if key == "paid_date" else Decimal(raw) if key == "amount" else raw
                for key in ("vendor", "cost_month", "bill_date", "quantity"):
                    raw = input(f"{key.replace('_', ' ')} [{fields[key] or 'none'}] (Enter unchanged, - clear): ").strip()
                    if raw == "-":
                        changes[key] = None
                    elif raw:
                        changes[key] = date.fromisoformat(raw) if key in {"cost_month", "bill_date"} else Decimal(raw) if key == "quantity" else raw
                edit_expense(db, args.expense_id, **changes)
            except (ValueError, InvalidOperation) as exc:
                parser.exit(2, f"homecost: error: {exc}\n")
        print(f"Updated expense {args.expense_id}.")
        return 0

    if args.command == "import":
        rows = []
        parse_errors = []
        try:
            with open(args.file, encoding="utf-8-sig", newline="") as source:
                reader = csv.DictReader(source)
                headers = set(reader.fieldnames or ())
                missing = {"paid_date", "amount"} - headers
                if missing:
                    parser.exit(2, "homecost: CSV header is missing required columns: " + ", ".join(sorted(missing)) + "\n")
                for row in reader:
                    line_number = reader.line_num
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
            errors = validate_expenses(db, rows, parse_errors)
            if errors:
                parser.exit(2, "homecost: import rejected; correct these rows and retry:\n" + "\n".join(errors) + "\n")
            accepted = []
            earlier_rows = []
            skipped = 0
            for line_number, fields in rows:
                duplicate_id = find_duplicate(db, fields)
                earlier_line = next(
                    (previous_line for previous_line, previous in earlier_rows if same_expense(fields, previous)),
                    None,
                )
                if duplicate_id is not None or earlier_line is not None:
                    if duplicate_id is not None:
                        match = db.execute(
                            """SELECT paid_date, cost_month, bill_date, category, amount, vendor, quantity,
                               payment_method FROM expenses WHERE id=?""",
                            [duplicate_id],
                        ).fetchone()
                        description = f"expense {duplicate_id}: {match}"
                    else:
                        match = next(fields for prior_line, fields in earlier_rows if prior_line == earlier_line)
                        description = f"CSV line {earlier_line}: {match}"
                    answer = input(f"Line {line_number} matches {description}. Import anyway? [yes/no]: ").strip().lower()
                    if answer != "yes":
                        skipped += 1
                        earlier_rows.append((line_number, fields))
                        continue
                accepted.append((line_number, fields))
                earlier_rows.append((line_number, fields))
            ids, errors = add_expenses(db, accepted)
        if errors:
            parser.exit(2, "homecost: import rejected; correct these rows and retry:\n" + "\n".join(errors) + "\n")
        print(f"Imported {len(ids)} expenses; skipped {skipped}.")
        return 0

    if args.command == "payment-methods" and args.payment_method_action == "add":
        home = Path.home() / ".homecost"
        home.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(home / "homecost.duckdb")) as db:
            try:
                name = _add_payment_method_flow(db)
            except ValueError as exc:
                parser.exit(2, f"homecost: error: {exc}\n")
        print(f"Added payment method {name}.")
        return 0

    if args.command == "categories" and args.category_action == "add":
        home = Path.home() / ".homecost"
        home.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(home / "homecost.duckdb")) as db:
            try:
                category = _add_category_flow(db)
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
            db.execute("BEGIN TRANSACTION")
            managed = ManagedTransaction(db)
            try:
                paid_date = _prompt_date(
                    "Paid date (YYYY-MM-DD): ",
                    error="Enter the paid date as YYYY-MM-DD (for example, 2025-09-15).",
                )
                amount = _prompt_amount()
                while True:
                    categories = managed.execute(
                        "SELECT name, unit FROM categories WHERE is_active AND name != 'unassigned' ORDER BY name"
                    ).fetchall()
                    labels = [row[0] for row in categories] + ["add a new category"]
                    category_index = _choice("Category number: ", labels)
                    if category_index == len(categories):
                        category = _add_category_flow(managed)
                        print(f"Added category {category}.")
                        continue
                    category, unit = categories[category_index]
                    break
                while True:
                    methods = [row[0] for row in managed.execute(
                        "SELECT name FROM payment_methods WHERE is_active AND name != 'unassigned' ORDER BY name"
                    ).fetchall()]
                    method_index = _choice(
                        "Payment method number: ",
                        methods + ["add a new payment method"],
                    )
                    if method_index == len(methods):
                        print(f"Added payment method {_add_payment_method_flow(managed)}.")
                        continue
                    payment_method = methods[method_index]
                    break

                vendors = [row[0] for row in managed.execute("SELECT name FROM vendors WHERE is_active ORDER BY name").fetchall()]
                vendor_index = _choice(
                    "Vendor number, or Enter to skip: ",
                    vendors + ["add a vendor"],
                    allow_empty=True,
                )
                if vendor_index is None:
                    vendor = None
                elif vendor_index == len(vendors):
                    vendor = add_vendor(managed, input("Vendor name: ").strip())
                else:
                    vendor = vendors[vendor_index]

                cost_month = _optional_month("Cost month (YYYY-MM, press Enter to use the paid month): ")
                bill_date = _prompt_date(
                    "Bill date (YYYY-MM-DD, Enter to skip): ",
                    allow_empty=True,
                    error="Enter the bill date as YYYY-MM-DD (for example, 2025-09-15).",
                )
                quantity = _prompt_quantity(unit) if unit else None
                fields = {
                    "paid_date": paid_date,
                    "category": category,
                    "amount": amount,
                    "payment_method": payment_method,
                    "vendor": vendor,
                    "cost_month": cost_month,
                    "bill_date": bill_date,
                    "quantity": quantity,
                }
                duplicate_id = find_duplicate(managed, fields)
                if duplicate_id is not None:
                    match = managed.execute(
                        """SELECT paid_date, cost_month, bill_date, category, amount, vendor, quantity,
                           payment_method FROM expenses WHERE id=?""",
                        [duplicate_id],
                    ).fetchone()
                    print(f"Possible duplicate: expense {duplicate_id}: {match}")
                    if input("Add anyway? [yes/no]: ").strip().lower() != "yes":
                        print("Expense not added.")
                        return 0
                expense_id = add_expense(managed, **fields)
                managed.execute("COMMIT")
            except KeyboardInterrupt:
                db.execute("ROLLBACK")
                print("Canceled - nothing was written.")
                return 0
            except (ValueError, InvalidOperation) as exc:
                db.execute("ROLLBACK")
                parser.exit(2, f"homecost: error: {exc}\n")
        print(f"Added expense {expense_id}.")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
