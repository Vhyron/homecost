from datetime import date
from decimal import Decimal

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
