from datetime import date
from decimal import Decimal

import duckdb
import pytest

from homecost.service import add_expense


def test_invalid_expense_rolls_back_initialization_and_seeds(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    with pytest.raises(ValueError, match="payment method"):
        add_expense(
            db,
            paid_date=date(2025, 1, 1),
            category="groceries",
            amount=Decimal("2.00"),
            payment_method="not-managed",
        )
    assert db.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='main'").fetchone()[0] == 0


def test_invalid_expense_leaves_existing_database_unchanged(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    db.execute("CREATE TABLE marker (value INTEGER)")
    db.execute("INSERT INTO marker VALUES (1)")
    with pytest.raises(ValueError, match="positive quantity"):
        add_expense(
            db,
            paid_date=date(2025, 1, 1),
            category="electricity",
            amount=Decimal("2.00"),
            payment_method="cash",
        )
    assert db.execute("SELECT value FROM marker").fetchone() == (1,)
    assert db.execute("SELECT count(*) FROM information_schema.tables WHERE table_name='expenses'").fetchone()[0] == 0
