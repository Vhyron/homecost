from datetime import date
from decimal import Decimal

import duckdb
import pytest

from homecost.service import add_expense, add_vendor, edit_expense, today_in_timezone


def create_expense(db):
    add_vendor(db, "market")
    today = today_in_timezone(db)
    return add_expense(
        db,
        paid_date=today,
        category="groceries",
        amount=Decimal("10.25"),
        payment_method="cash",
        vendor="market",
        cost_month=today.replace(day=1),
        bill_date=today,
    )


def test_edit_preserves_id_and_unchanged_fields(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    expense_id = create_expense(db)

    assert edit_expense(db, expense_id, amount=Decimal("12.00")) == expense_id
    row = db.execute(
        "SELECT id, paid_date, category, amount, vendor, cost_month, bill_date, payment_method "
        "FROM expenses WHERE id=?", [expense_id]
    ).fetchone()
    today = today_in_timezone(db)
    assert row == (
        expense_id, today, "groceries", Decimal("12.00"), "market",
        today.replace(day=1), today, "cash"
    )


def test_invalid_edit_leaves_original_expense_unchanged(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    expense_id = create_expense(db)
    before = db.execute("SELECT * FROM expenses WHERE id=?", [expense_id]).fetchone()

    with pytest.raises(ValueError, match="positive Decimal"):
        edit_expense(db, expense_id, amount=Decimal("0"))

    assert db.execute("SELECT * FROM expenses WHERE id=?", [expense_id]).fetchone() == before


def test_edit_rejects_unknown_expense_id(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    with pytest.raises(ValueError, match="does not exist"):
        edit_expense(db, 10, amount=Decimal("1.00"))
