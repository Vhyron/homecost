from datetime import date
from decimal import Decimal

import duckdb

from homecost.db import initialize


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
    if amount != amount.quantize(Decimal("0.01")):
        raise ValueError("amount must have at most two decimal places")
    cost_month = cost_month or paid_date.replace(day=1)
    cost_month = cost_month.replace(day=1)
    initialize(db)
    result = db.execute(
        """INSERT INTO expenses (paid_date, category, amount, vendor, cost_month, bill_date)
           VALUES (?, ?, ?, ?, ?, ?) RETURNING id""",
        [paid_date, category, amount, vendor, cost_month, bill_date],
    ).fetchone()
    return result[0]
