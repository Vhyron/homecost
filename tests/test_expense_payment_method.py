from datetime import date
from decimal import Decimal

import duckdb
import pytest

from homecost.service import add_expense


def test_expense_requires_managed_payment_method(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    with pytest.raises(ValueError, match="payment method"):
        add_expense(
            db,
            paid_date=date(2025, 1, 1),
            category="groceries",
            amount=Decimal("1.00"),
            payment_method="not-managed",
        )
    assert db.execute("SELECT count(*) FROM expenses").fetchone()[0] == 0


def test_expense_accepts_managed_payment_method(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    add_expense(
        db,
        paid_date=date(2025, 1, 1),
        category="groceries",
        amount=Decimal("1.00"),
        payment_method="cash",
    )
    assert db.execute("SELECT payment_method FROM expenses").fetchone() == ("cash",)
