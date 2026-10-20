from datetime import date
from decimal import Decimal

import duckdb
import pytest

from homecost.service import add_expense


def add(db, category, quantity):
    return add_expense(
        db,
        paid_date=date(2025, 1, 1),
        category=category,
        amount=Decimal("1.00"),
        payment_method="cash",
        quantity=quantity,
    )


def test_metered_expense_requires_positive_quantity(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    with pytest.raises(ValueError, match="positive quantity"):
        add(db, "electricity", None)
    with pytest.raises(ValueError, match="positive quantity"):
        add(db, "electricity", Decimal("0"))


def test_metered_expense_stores_quantity_to_three_places(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    add(db, "electricity", Decimal("12.345"))
    assert db.execute("SELECT quantity FROM expenses").fetchone() == (Decimal("12.345"),)


def test_quantity_rejects_precision_over_three_places(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    with pytest.raises(ValueError, match="at most three decimal places"):
        add(db, "electricity", Decimal("1.0001"))


def test_non_metered_expense_rejects_quantity(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    with pytest.raises(ValueError, match="does not use quantity"):
        add(db, "groceries", Decimal("5"))
