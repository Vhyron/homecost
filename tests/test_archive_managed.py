from datetime import date
from decimal import Decimal

import duckdb
import pytest

from homecost.service import (
    add_expense,
    add_payment_method,
    add_vendor,
    archive_managed_value,
    today_in_timezone,
)


def test_archive_preserves_expense_history_and_reports_use_count(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    add_vendor(db, "market")
    add_payment_method(db, "wallet")
    add_expense(
        db,
        paid_date=today_in_timezone(db),
        category="groceries",
        amount=Decimal("1.00"),
        payment_method="wallet",
        vendor="market",
    )

    assert archive_managed_value(db, "category", "groceries") == 1
    assert archive_managed_value(db, "vendor", "market") == 1
    assert archive_managed_value(db, "payment_method", "wallet") == 1
    assert db.execute("SELECT category, vendor, payment_method FROM expenses").fetchone() == (
        "groceries", "market", "wallet"
    )
    assert db.execute("SELECT is_active FROM categories WHERE name='groceries'").fetchone() == (False,)
    assert db.execute("SELECT is_active FROM vendors WHERE name='market'").fetchone() == (False,)
    assert db.execute("SELECT is_active FROM payment_methods WHERE name='wallet'").fetchone() == (False,)


@pytest.mark.parametrize("kind", ["category", "vendor", "payment_method"])
def test_archived_values_cannot_be_used_for_new_expenses(tmp_path, kind):
    db = duckdb.connect(str(tmp_path / f"{kind}.duckdb"))
    add_vendor(db, "market")
    add_payment_method(db, "wallet")
    archive_name = {"category": "groceries", "vendor": "market", "payment_method": "wallet"}[kind]
    archive_managed_value(db, kind, archive_name)
    args = dict(
        paid_date=today_in_timezone(db),
        category="groceries" if kind != "category" else archive_name,
        amount=Decimal("1.00"),
        payment_method="wallet" if kind == "payment_method" else "cash",
        vendor="market" if kind == "vendor" else None,
    )
    with pytest.raises(ValueError, match="not active"):
        add_expense(db, **args)


def test_reserved_unassigned_values_cannot_be_archived(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    with pytest.raises(ValueError, match="reserved"):
        archive_managed_value(db, "category", "unassigned")
    with pytest.raises(ValueError, match="reserved"):
        archive_managed_value(db, "payment_method", "unassigned")
