from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import duckdb

from homecost.db import initialize


def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        raise ValueError("name is required")
    normalized = " ".join(name.split()).lower()
    if not normalized:
        raise ValueError("name is required")
    return normalized


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
    if db.execute("SELECT 1 FROM categories WHERE name = ?", [normalized]).fetchone():
        raise ValueError(f"category {normalized!r} already exists")
    db.execute(
        "INSERT INTO categories (name, unit, monthly_bill_expected) VALUES (?, ?, ?)",
        [normalized, unit, monthly_bill_expected],
    )
    return normalized


def add_vendor(db: duckdb.DuckDBPyConnection, name: str) -> str:
    normalized = normalize_name(name)
    initialize(db)
    if db.execute("SELECT 1 FROM vendors WHERE name = ?", [normalized]).fetchone():
        raise ValueError(f"vendor {normalized!r} already exists")
    db.execute("INSERT INTO vendors (name) VALUES (?)", [normalized])
    return normalized


def add_payment_method(db: duckdb.DuckDBPyConnection, name: str) -> str:
    normalized = normalize_name(name)
    initialize(db)
    if db.execute("SELECT 1 FROM payment_methods WHERE name = ?", [normalized]).fetchone():
        raise ValueError(f"payment method {normalized!r} already exists")
    db.execute("INSERT INTO payment_methods (name) VALUES (?)", [normalized])
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
        "SELECT unit FROM categories WHERE name = ?", [normalized_category]
    ).fetchone()
    if not category_row:
        raise ValueError(f"category {category!r} is not managed; add/reactivate it or correct the CSV")
    if category_row[0]:
        if not isinstance(quantity, Decimal) or not quantity.is_finite() or quantity <= 0:
            raise ValueError("metered categories require a positive quantity")
        if quantity != quantity.quantize(Decimal("0.001")):
            raise ValueError("quantity must have at most three decimal places")
    elif quantity is not None:
        raise ValueError("this category does not use quantity")
    if normalized_vendor and not db.execute(
        "SELECT 1 FROM vendors WHERE name = ?", [normalized_vendor]
    ).fetchone():
        raise ValueError(f"vendor {vendor!r} is not managed; add/reactivate it or correct the CSV")
    if not db.execute("SELECT 1 FROM payment_methods WHERE name = ?", [normalized_method]).fetchone():
        raise ValueError(f"payment method {payment_method!r} is not managed; add/reactivate it or correct the CSV")
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
