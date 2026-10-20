from datetime import date
from decimal import Decimal

import duckdb
import pytest

from homecost.service import add_expense


def test_add_expense_defaults_cost_month_to_paid_month(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    expense_id = add_expense(
        db,
        paid_date=date(2025, 3, 12),
        category="groceries",
        amount=Decimal("12.50"),
    )
    row = db.execute(
        "SELECT paid_date, category, amount, vendor, cost_month, bill_date "
        "FROM expenses WHERE id = ?", [expense_id]
    ).fetchone()
    assert row == (date(2025, 3, 12), "groceries", Decimal("12.50"), None,
                   date(2025, 3, 1), None)


def test_add_expense_accepts_cost_month_and_bill_date_independently(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    expense_id = add_expense(
        db,
        paid_date=date(2025, 4, 2),
        category="electricity",
        amount=Decimal("30.00"),
        cost_month=date(2025, 3, 1),
        bill_date=date(2025, 3, 20),
    )
    assert db.execute(
        "SELECT cost_month, bill_date FROM expenses WHERE id = ?", [expense_id]
    ).fetchone() == (date(2025, 3, 1), date(2025, 3, 20))


@pytest.mark.parametrize("field,value", [("paid_date", None), ("category", ""), ("amount", Decimal("0"))])
def test_add_expense_rejects_missing_required_fields(tmp_path, field, value):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    fields = dict(paid_date=date(2025, 3, 12), category="groceries", amount=Decimal("12.50"))
    fields[field] = value
    with pytest.raises(ValueError):
        add_expense(db, **fields)
    assert db.execute("SELECT count(*) FROM information_schema.tables WHERE table_name='expenses'").fetchone()[0] == 0
