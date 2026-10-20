from datetime import date
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


def add_category(db: duckdb.DuckDBPyConnection, name: str, unit: str | None = None) -> str:
    normalized = normalize_name(name)
    initialize(db)
    if db.execute("SELECT 1 FROM categories WHERE name = ?", [normalized]).fetchone():
        raise ValueError(f"category {normalized!r} already exists")
    db.execute("INSERT INTO categories (name, unit) VALUES (?, ?)", [normalized, unit])
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
    if not isinstance(paid_date, date):
        raise ValueError("paid_date is required")
    if not isinstance(category, str) or not category.strip():
        raise ValueError("category is required")
    if not isinstance(amount, Decimal) or amount <= 0:
        raise ValueError("amount must be a positive Decimal")
    if amount != amount.quantize(Decimal("0.01")):
        raise ValueError("amount must have at most two decimal places")
    cost_month = cost_month or paid_date.replace(day=1)
    cost_month = cost_month.replace(day=1)
    normalized_method = normalize_name(payment_method)
    initialize(db)
    category_row = db.execute("SELECT unit FROM categories WHERE name = ?", [category]).fetchone()
    if category_row and category_row[0]:
        if not isinstance(quantity, Decimal) or quantity <= 0:
            raise ValueError("metered categories require a positive quantity")
        if quantity != quantity.quantize(Decimal("0.001")):
            raise ValueError("quantity must have at most three decimal places")
    elif quantity is not None:
        raise ValueError("this category does not use quantity")
    if not db.execute("SELECT 1 FROM payment_methods WHERE name = ?", [normalized_method]).fetchone():
        raise ValueError(f"payment method {normalized_method!r} is not managed; add it first")
    result = db.execute(
        """INSERT INTO expenses
           (paid_date, category, amount, vendor, cost_month, bill_date, payment_method, quantity)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
        [paid_date, category, amount, vendor, cost_month, bill_date, normalized_method, quantity],
    ).fetchone()
    return result[0]
