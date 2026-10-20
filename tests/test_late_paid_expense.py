from datetime import date
from decimal import Decimal

import duckdb

from homecost.service import add_expense


def test_late_paid_utility_stays_in_assigned_cost_month(tmp_path, monkeypatch):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    monkeypatch.setattr("homecost.service.today_in_timezone", lambda db: date(2025, 10, 20))
    add_expense(
        db,
        paid_date=date(2025, 10, 15),
        category="electricity",
        amount=Decimal("45.00"),
        payment_method="cash",
        cost_month=date(2025, 9, 1),
        bill_date=date(2025, 9, 8),
        quantity=Decimal("120.5"),
    )
    assert db.execute("SELECT paid_date, cost_month, bill_date FROM expenses").fetchone() == (
        date(2025, 10, 15), date(2025, 9, 1), date(2025, 9, 8)
    )
