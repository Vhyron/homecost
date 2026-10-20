from datetime import date
from decimal import Decimal

import duckdb
import pytest

from homecost.service import add_expense


def test_expense_preserves_decimal_amount(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    add_expense(db, paid_date=date(2025, 1, 1), category="groceries", amount=Decimal("123.45"), payment_method="cash")
    value = db.execute("SELECT amount FROM expenses").fetchone()[0]
    assert value == Decimal("123.45")


@pytest.mark.parametrize("amount", [Decimal("1.001"), Decimal("0.0001")])
def test_expense_rejects_more_than_two_decimal_places(tmp_path, amount):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    with pytest.raises(ValueError, match="at most two decimal places"):
        add_expense(db, paid_date=date(2025, 1, 1), category="groceries", amount=amount, payment_method="cash")
    assert db.execute("SELECT count(*) FROM information_schema.tables WHERE table_name='expenses'").fetchone()[0] == 0
