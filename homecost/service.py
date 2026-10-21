from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import duckdb

from homecost.db import initialize


def _match_values(fields):
    paid_date = fields["paid_date"]
    return (
        paid_date,
        paid_date.replace(day=1) if fields.get("cost_month") is None else fields["cost_month"].replace(day=1),
        fields.get("bill_date"),
        normalize_name(fields["category"]),
        fields["amount"],
        normalize_name(fields["vendor"]) if fields.get("vendor") else None,
        fields.get("quantity"),
        normalize_name(fields["payment_method"]),
    )


def same_expense(first, second) -> bool:
    return _match_values(first) == _match_values(second)


def find_duplicate(db: duckdb.DuckDBPyConnection, fields) -> int | None:
    initialize(db)
    duplicate = db.execute(
        """SELECT id FROM expenses WHERE paid_date=? AND cost_month=?
           AND bill_date IS NOT DISTINCT FROM ? AND category=? AND amount=?
           AND vendor IS NOT DISTINCT FROM ? AND quantity IS NOT DISTINCT FROM ?
           AND payment_method=? ORDER BY id LIMIT 1""",
        _match_values(fields),
    ).fetchone()
    return duplicate[0] if duplicate else None


def parse_period(period: str):
    """Return (start, end_exclusive) for 'YYYY-MM', 'YYYY-Qn', or 'YYYY'."""
    if not isinstance(period, str):
        raise ValueError("period must be YYYY-MM, YYYY-Qn, or YYYY")
    if "-Q" in period:
        year, _, quarter = period.partition("-Q")
        if len(year) != 4 or not year.isdigit() or quarter not in {"1", "2", "3", "4"}:
            raise ValueError("period must be YYYY-MM, YYYY-Qn, or YYYY")
        start_month = (int(quarter) - 1) * 3 + 1
        start = date(int(year), start_month, 1)
    elif "-" in period:
        year, _, month = period.partition("-")
        if len(year) != 4 or len(month) != 2 or not year.isdigit() or not month.isdigit() or not 1 <= int(month) <= 12:
            raise ValueError("period must be YYYY-MM, YYYY-Qn, or YYYY")
        start = date(int(year), int(month), 1)
    elif len(period) == 4 and period.isdigit():
        start = date(int(period), 1, 1)
    else:
        raise ValueError("period must be YYYY-MM, YYYY-Qn, or YYYY")
    if period.isdigit():  # YYYY
        end = date(start.year + 1, 1, 1)
    elif "-Q" in period:
        end = date(start.year + 1, 1, 1) if start.month == 10 else date(start.year, start.month + 3, 1)
    else:
        end = date(start.year + 1, 1, 1) if start.month == 12 else date(start.year, start.month + 1, 1)
    return start, end


def category_totals(
    db: duckdb.DuckDBPyConnection,
    period: str,
    basis: str = "cost_month",
) -> list[tuple[str, Decimal]]:
    start, end = parse_period(period)
    if basis not in {"cost_month", "paid_date"}:
        raise ValueError("basis must be cost_month or paid_date")
    initialize(db)
    column = basis
    return db.execute(
        f"""SELECT category, SUM(amount) FROM expenses
            WHERE {column} >= ? AND {column} < ? GROUP BY category ORDER BY category""",
        [start, end],
    ).fetchall()


def metered_summary(
    db: duckdb.DuckDBPyConnection,
    period: str,
    basis: str = "cost_month",
) -> list[tuple]:
    if not (period.count("-") == 1 and "-Q" not in period):
        raise ValueError("metered summaries compare single months")
    start, end = parse_period(period)
    if start.month == 1:
        previous_start, previous_end = date(start.year - 1, 12, 1), date(start.year, 1, 1)
    else:
        previous_start, previous_end = date(start.year, start.month - 1, 1), start
    if basis not in {"cost_month", "paid_date"}:
        raise ValueError("basis must be cost_month or paid_date")
    initialize(db)
    rows = db.execute(
        f"""SELECT category, SUM(amount), SUM(quantity) FROM expenses
            WHERE quantity IS NOT NULL AND {basis} >= ? AND {basis} < ?
            GROUP BY category ORDER BY category""",
        [start, end],
    ).fetchall()
    previous = {
        category: (usage, total)
        for category, usage, total in db.execute(
            f"""SELECT category, SUM(quantity), SUM(amount) FROM expenses
                WHERE quantity IS NOT NULL AND {basis} >= ? AND {basis} < ?
                GROUP BY category""",
            [previous_start, previous_end],
        ).fetchall()
    }
    summary = []
    for category, total, quantity in rows:
        unit_cost = (total / quantity).quantize(Decimal("0.01"))
        previous_usage, previous_total = previous.get(category, (None, None))
        if previous_usage is None:
            summary.append((category, total, quantity, unit_cost, None, None))
        else:
            previous_unit = (previous_total / previous_usage).quantize(Decimal("0.01"))
            summary.append((
                category, total, quantity, unit_cost,
                quantity - previous_usage, unit_cost - previous_unit,
            ))
    return summary


def grocery_trip_summary(
    db: duckdb.DuckDBPyConnection,
    period: str,
    basis: str = "cost_month",
) -> tuple[int, Decimal] | None:
    start, end = parse_period(period)
    if basis not in {"cost_month", "paid_date"}:
        raise ValueError("basis must be cost_month or paid_date")
    initialize(db)
    trips, average = db.execute(
        f"""SELECT count(*), AVG(amount) FROM expenses
            WHERE category='groceries' AND {basis} >= ? AND {basis} < ?""",
        [start, end],
    ).fetchone()
    return (trips, Decimal(str(average)).quantize(Decimal("0.01"))) if trips else None


def is_current_period(db: duckdb.DuckDBPyConnection, period: str) -> bool:
    today = today_in_timezone(db)
    start, end = parse_period(period)
    return start <= today < end


def month_detail(
    db: duckdb.DuckDBPyConnection,
    period: str,
    basis: str = "cost_month",
) -> list[tuple[date, str, Decimal]]:
    start, end = parse_period(period)
    if basis not in {"cost_month", "paid_date"}:
        raise ValueError("basis must be cost_month or paid_date")
    initialize(db)
    column = basis
    month_column = f"date_trunc('month', {column})"
    return db.execute(
        f"""SELECT {month_column}, category, SUM(amount) FROM expenses
            WHERE {column} >= ? AND {column} < ? GROUP BY 1, 2 ORDER BY 1, 2""",
        [start, end],
    ).fetchall()


def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        raise ValueError("name is required")
    normalized = " ".join(name.split()).lower()
    if not normalized:
        raise ValueError("name is required")
    return normalized


def archive_managed_value(
    db: duckdb.DuckDBPyConnection,
    kind: str,
    name: str,
) -> int:
    lists = {
        "category": ("categories", "category"),
        "vendor": ("vendors", "vendor"),
        "payment_method": ("payment_methods", "payment_method"),
    }
    if kind not in lists:
        raise ValueError(f"unsupported managed list {kind!r}")
    table, column = lists[kind]
    name = normalize_name(name)
    if kind != "vendor" and name == "unassigned":
        raise ValueError("unassigned is reserved and cannot be removed")
    db.execute("BEGIN TRANSACTION")
    try:
        initialize(db)
        if not db.execute(f"SELECT 1 FROM {table} WHERE name=?", [name]).fetchone():
            raise ValueError(f"{kind} {name!r} does not exist")
        count = db.execute(f"SELECT count(*) FROM expenses WHERE {column}=?", [name]).fetchone()[0]
        db.execute(f"UPDATE {table} SET is_active=FALSE WHERE name=?", [name])
        db.execute("COMMIT")
        return count
    except Exception:
        db.execute("ROLLBACK")
        raise


def rename_managed_value(
    db: duckdb.DuckDBPyConnection,
    kind: str,
    old_name: str,
    new_name: str,
) -> int:
    lists = {
        "category": ("categories", "category"),
        "vendor": ("vendors", "vendor"),
        "payment_method": ("payment_methods", "payment_method"),
    }
    if kind not in lists:
        raise ValueError(f"unsupported managed list {kind!r}")
    table, column = lists[kind]
    old_name, new_name = normalize_name(old_name), normalize_name(new_name)
    if kind != "vendor" and (old_name == "unassigned" or new_name == "unassigned"):
        raise ValueError("unassigned is reserved and cannot be renamed")
    db.execute("BEGIN TRANSACTION")
    try:
        initialize(db)
        if not db.execute(f"SELECT 1 FROM {table} WHERE name=?", [old_name]).fetchone():
            raise ValueError(f"{kind} {old_name!r} does not exist")
        if old_name == new_name:
            db.execute("COMMIT")
            return 0
        if db.execute(f"SELECT 1 FROM {table} WHERE name=?", [new_name]).fetchone():
            raise ValueError(f"{kind} {new_name!r} already exists")
        count = db.execute(f"SELECT count(*) FROM expenses WHERE {column}=?", [old_name]).fetchone()[0]
        db.execute(f"UPDATE expenses SET {column}=? WHERE {column}=?", [new_name, old_name])
        db.execute(f"UPDATE {table} SET name=? WHERE name=?", [new_name, old_name])
        db.execute("COMMIT")
        return count
    except Exception:
        db.execute("ROLLBACK")
        raise


def list_managed_values(db: duckdb.DuckDBPyConnection, kind: str) -> list[tuple[str, str]]:
    tables = {"category": "categories", "vendor": "vendors", "payment_method": "payment_methods"}
    if kind not in tables:
        raise ValueError(f"unsupported managed list {kind!r}")
    initialize(db)
    return [
        (name, "active" if active else "archived")
        for name, active in db.execute(
            f"SELECT name, is_active FROM {tables[kind]} ORDER BY name"
        ).fetchall()
    ]


def add_category(
    db: duckdb.DuckDBPyConnection,
    name: str,
    unit: str | None,
    monthly_bill_expected: bool,
) -> str:
    normalized = normalize_name(name)
    if not isinstance(monthly_bill_expected, bool):
        raise ValueError("monthly_bill_expected must be yes or no")
    initialize(db)
    existing = db.execute("SELECT is_active FROM categories WHERE name = ?", [normalized]).fetchone()
    if existing:
        if existing[0]:
            raise ValueError(f"category {normalized!r} already exists")
        db.execute("UPDATE categories SET is_active=TRUE WHERE name=?", [normalized])
        return normalized
    db.execute(
        "INSERT INTO categories (name, unit, monthly_bill_expected, is_active) VALUES (?, ?, ?, TRUE)",
        [normalized, unit, monthly_bill_expected],
    )
    return normalized


def add_vendor(db: duckdb.DuckDBPyConnection, name: str) -> str:
    normalized = normalize_name(name)
    initialize(db)
    existing = db.execute("SELECT is_active FROM vendors WHERE name = ?", [normalized]).fetchone()
    if existing:
        if existing[0]:
            raise ValueError(f"vendor {normalized!r} already exists")
        db.execute("UPDATE vendors SET is_active=TRUE WHERE name=?", [normalized])
        return normalized
    db.execute("INSERT INTO vendors (name, is_active) VALUES (?, TRUE)", [normalized])
    return normalized


def add_payment_method(db: duckdb.DuckDBPyConnection, name: str) -> str:
    normalized = normalize_name(name)
    initialize(db)
    existing = db.execute("SELECT is_active FROM payment_methods WHERE name = ?", [normalized]).fetchone()
    if existing:
        if existing[0]:
            raise ValueError(f"payment method {normalized!r} already exists")
        db.execute("UPDATE payment_methods SET is_active=TRUE WHERE name=?", [normalized])
        return normalized
    db.execute("INSERT INTO payment_methods (name, is_active) VALUES (?, TRUE)", [normalized])
    return normalized


def get_settings(db: duckdb.DuckDBPyConnection) -> dict[str, str]:
    initialize(db)
    return dict(db.execute("SELECT key, value FROM settings").fetchall())


_CURRENCIES = set("AED AFN ALL AMD ANG AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD BND BOB BRL BSD BTN BWP BYN BZD CAD CDF CHF CLP CNY COP CRC CUP CVE CZK DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP GBP GEL GHS GIP GMD GNF GTQ GYD HKD HNL HTG HUF IDR ILS INR IQD IRR ISK JMD JOD JPY KES KGS KHR KMF KPW KRW KWD KYD KZT LAK LBP LKR LRD LSL LYD MAD MDL MGA MKD MMK MNT MOP MRU MUR MVR MWK MXN MYR MZN NAD NGN NIO NOK NPR NZD OMR PAB PEN PGK PHP PKR PLN PYG QAR RON RSD RUB RWF SAR SBD SCR SDG SEK SGD SHP SLE SLL SOS SRD SSP STN SVC SYP SZL THB TJS TMT TND TOP TRY TTD TWD TZS UAH UGX USD UYU UZS VES VND VUV WST XAF XCD XOF XPF YER ZAR ZMW ZWL".split())


def today_in_timezone(db: duckdb.DuckDBPyConnection) -> date:
    timezone = get_settings(db)["timezone"]
    return datetime.now(ZoneInfo(timezone)).date()


def set_setting(
    db: duckdb.DuckDBPyConnection,
    key: str,
    value: str,
    *,
    confirm_timezone: bool = False,
) -> None:
    initialize(db)
    if key not in {"timezone", "currency", "backup-retention"}:
        raise ValueError(f"unsupported setting {key!r}")
    if key == "timezone":
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("timezone must be a valid IANA time-zone name") from None
        if not confirm_timezone:
            raise ValueError("changing the time zone requires confirmation")
    elif key == "currency":
        value = value.upper()
        if value not in _CURRENCIES:
            raise ValueError("currency must be a valid ISO 4217 code")
        if db.execute("SELECT count(*) FROM expenses").fetchone()[0]:
            raise ValueError("currency cannot change after the first expense")
    else:
        try:
            retention = int(value)
        except ValueError:
            raise ValueError("backup-retention must be an integer from 1 to 365") from None
        if str(retention) != value or not 1 <= retention <= 365:
            raise ValueError("backup-retention must be an integer from 1 to 365")
    db.execute("UPDATE settings SET value = ? WHERE key = ?", [value, key])


def _add_expense(
    db: duckdb.DuckDBPyConnection,
    *,
    paid_date: date,
    category: str,
    amount: Decimal,
    payment_method: str,
    vendor: str | None = None,
    cost_month: date | None = None,
    bill_date: date | None = None,
    quantity: Decimal | None = None,
    _expense_id: int | None = None,
) -> int:
    if not isinstance(paid_date, date):
        raise ValueError("paid_date is required")
    if not isinstance(category, str) or not category.strip():
        raise ValueError("category is required")
    if not isinstance(amount, Decimal) or not amount.is_finite() or amount <= 0:
        raise ValueError("amount must be a positive Decimal")
    if amount != amount.quantize(Decimal("0.01")):
        raise ValueError("amount must have at most two decimal places")
    cost_month = cost_month or paid_date.replace(day=1)
    cost_month = cost_month.replace(day=1)
    normalized_category = normalize_name(category)
    normalized_method = normalize_name(payment_method)
    normalized_vendor = normalize_name(vendor) if vendor is not None else None
    initialize(db)
    if paid_date > today_in_timezone(db):
        raise ValueError("paid_date cannot be later than today in the household time zone")
    month_gap = (paid_date.year - cost_month.year) * 12 + paid_date.month - cost_month.month
    if abs(month_gap) > 12:
        raise ValueError("paid_date and cost_month cannot be more than 12 calendar months apart")
    category_row = db.execute(
        "SELECT unit, is_active FROM categories WHERE name = ?", [normalized_category]
    ).fetchone()
    if not category_row:
        raise ValueError(f"category {category!r} is not managed; add/reactivate it or correct the CSV")
    if not category_row[1]:
        raise ValueError(f"category {category!r} is not active; reactivate it first")
    if category_row[0]:
        if not isinstance(quantity, Decimal) or not quantity.is_finite() or quantity <= 0:
            raise ValueError("metered categories require a positive quantity")
        if quantity != quantity.quantize(Decimal("0.001")):
            raise ValueError("quantity must have at most three decimal places")
    elif quantity is not None:
        raise ValueError("this category does not use quantity")
    vendor_row = db.execute(
        "SELECT is_active FROM vendors WHERE name = ?", [normalized_vendor]
    ).fetchone() if normalized_vendor else None
    if normalized_vendor and not vendor_row:
        raise ValueError(f"vendor {vendor!r} is not managed; add/reactivate it or correct the CSV")
    if vendor_row and not vendor_row[0]:
        raise ValueError(f"vendor {vendor!r} is not active; reactivate it first")
    method_row = db.execute("SELECT is_active FROM payment_methods WHERE name = ?", [normalized_method]).fetchone()
    if not method_row:
        raise ValueError(f"payment method {payment_method!r} is not managed; add/reactivate it or correct the CSV")
    if not method_row[0]:
        raise ValueError(f"payment method {payment_method!r} is not active; reactivate it first")
    values = [paid_date, normalized_category, amount, normalized_vendor, cost_month, bill_date, normalized_method, quantity]
    if _expense_id is None:
        result = db.execute(
            """INSERT INTO expenses
               (paid_date, category, amount, vendor, cost_month, bill_date, payment_method, quantity)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
            values,
        ).fetchone()
        return result[0]
    db.execute(
        """UPDATE expenses SET paid_date=?, category=?, amount=?, vendor=?, cost_month=?, bill_date=?,
           payment_method=?, quantity=? WHERE id=?""",
        [*values, _expense_id],
    )
    return _expense_id


def validate_expenses(db: duckdb.DuckDBPyConnection, rows, parse_errors=()):
    db.execute("BEGIN TRANSACTION")
    errors = list(parse_errors)
    try:
        for line_number, fields in rows:
            try:
                _add_expense(db, **fields)
            except ValueError as exc:
                errors.append(f"line {line_number}: {exc}")
        db.execute("ROLLBACK")
        return errors
    except Exception:
        db.execute("ROLLBACK")
        raise


def add_expenses(db: duckdb.DuckDBPyConnection, rows, parse_errors=()):
    db.execute("BEGIN TRANSACTION")
    errors = list(parse_errors)
    ids = []
    try:
        for line_number, fields in rows:
            try:
                ids.append(_add_expense(db, **fields))
            except ValueError as exc:
                errors.append(f"line {line_number}: {exc}")
        if errors:
            db.execute("ROLLBACK")
            return [], errors
        db.execute("COMMIT")
        return ids, []
    except Exception:
        db.execute("ROLLBACK")
        raise


def list_expenses(
    db: duckdb.DuckDBPyConnection,
    *,
    category: str | None = None,
    payment_method: str | None = None,
) -> list:
    initialize(db)
    query = """SELECT id, paid_date, category, amount, vendor, cost_month, bill_date,
              payment_method, quantity FROM expenses"""
    conditions, values = [], []
    if category is not None:
        conditions.append("category=?")
        values.append(normalize_name(category))
    if payment_method is not None:
        conditions.append("payment_method=?")
        values.append(normalize_name(payment_method))
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    return db.execute(query + " ORDER BY id", values).fetchall()


def delete_expense(db: duckdb.DuckDBPyConnection, expense_id: int) -> None:
    db.execute("BEGIN TRANSACTION")
    try:
        initialize(db)
        deleted = db.execute("DELETE FROM expenses WHERE id=? RETURNING id", [expense_id]).fetchone()
        if deleted is None:
            raise ValueError(f"expense {expense_id} does not exist")
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")
        raise


def edit_expense(db: duckdb.DuckDBPyConnection, expense_id: int, **changes) -> int:
    allowed = {"paid_date", "category", "amount", "payment_method", "vendor", "cost_month", "bill_date", "quantity"}
    if changes.keys() - allowed:
        raise ValueError("edit contains unsupported expense fields")
    db.execute("BEGIN TRANSACTION")
    try:
        initialize(db)
        row = db.execute(
            """SELECT paid_date, category, amount, payment_method, vendor, cost_month, bill_date, quantity
               FROM expenses WHERE id=?""",
            [expense_id],
        ).fetchone()
        if row is None:
            raise ValueError(f"expense {expense_id} does not exist")
        fields = dict(zip(
            ("paid_date", "category", "amount", "payment_method", "vendor", "cost_month", "bill_date", "quantity"),
            row,
        ))
        fields.update(changes)
        result = _add_expense(db, **fields, _expense_id=expense_id)
        db.execute("COMMIT")
        return result
    except Exception:
        db.execute("ROLLBACK")
        raise


def add_expense(
    db: duckdb.DuckDBPyConnection,
    *,
    paid_date: date,
    category: str,
    amount: Decimal,
    payment_method: str,
    vendor: str | None = None,
    cost_month: date | None = None,
    bill_date: date | None = None,
    quantity: Decimal | None = None,
) -> int:
    db.execute("BEGIN TRANSACTION")
    try:
        result = _add_expense(
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
        db.execute("COMMIT")
        return result
    except Exception:
        db.execute("ROLLBACK")
        raise
