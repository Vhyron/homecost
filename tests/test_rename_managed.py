from datetime import date
from decimal import Decimal

import duckdb
import pytest

from homecost.service import add_expense, add_vendor, rename_managed_value, today_in_timezone


def test_rename_updates_managed_value_and_all_expenses(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    add_vendor(db, "market")
    today = today_in_timezone(db)
    add_expense(
        db,
        paid_date=today,
        category="groceries",
        amount=Decimal("1.00"),
        payment_method="cash",
        vendor="market",
    )

    assert rename_managed_value(db, "category", "groceries", " Food Store ") == 1
    assert rename_managed_value(db, "vendor", "market", "Online Shop") == 1
    assert rename_managed_value(db, "payment_method", "cash", "Card") == 1
    assert db.execute("SELECT category, vendor, payment_method FROM expenses").fetchone() == (
        "food store", "online shop", "card"
    )
    assert db.execute("SELECT name FROM categories WHERE name='food store'").fetchone() == ("food store",)


def test_rename_rejects_normalized_duplicates_and_reserved_values(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    with pytest.raises(ValueError, match="already exists"):
        rename_managed_value(db, "category", "groceries", " ELECTRICITY ")
    with pytest.raises(ValueError, match="reserved"):
        rename_managed_value(db, "category", "unassigned", "missing")
    with pytest.raises(ValueError, match="reserved"):
        rename_managed_value(db, "payment_method", "cash", " UNASSIGNED ")


def test_rename_requires_existing_old_name(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    with pytest.raises(ValueError, match="does not exist"):
        rename_managed_value(db, "vendor", "unknown", "known")
