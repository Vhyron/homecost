from datetime import date
from decimal import Decimal

import duckdb


def add_expense(
    db: duckdb.DuckDBPyConnection,
    *,
    paid_date: date,
    category: str,
    amount: Decimal,
    vendor: str | None = None,
    cost_month: date | None = None,
    bill_date: date | None = None,
) -> int:
    if not isinstance(paid_date, date):
        raise ValueError("paid_date is required")
    if not isinstance(category, str) or not category.strip():
        raise ValueError("category is required")
    if not isinstance(amount, Decimal) or amount <= 0:
        raise ValueError("amount must be a positive Decimal")
    cost_month = cost_month or paid_date.replace(day=1)
    cost_month = cost_month.replace(day=1)
    db.execute("CREATE SEQUENCE IF NOT EXISTS expense_id_seq START 1")
    db.execute(
        """CREATE TABLE IF NOT EXISTS expenses (
            id BIGINT PRIMARY KEY DEFAULT nextval('expense_id_seq'),
            paid_date DATE NOT NULL,
            category VARCHAR NOT NULL,
            amount DECIMAL(18, 2) NOT NULL,
            vendor VARCHAR,
            cost_month DATE NOT NULL,
            bill_date DATE
        )"""
    )
    result = db.execute(
        """INSERT INTO expenses (paid_date, category, amount, vendor, cost_month, bill_date)
           VALUES (?, ?, ?, ?, ?, ?) RETURNING id""",
        [paid_date, category, amount, vendor, cost_month, bill_date],
    ).fetchone()
    return result[0]
