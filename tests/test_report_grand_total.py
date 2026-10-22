from datetime import date
from decimal import Decimal

import duckdb

from homecost.cli import main
from homecost.service import add_expense, period_total


def seed(db):
    add_expense(db, paid_date=date(2025, 1, 5), category="groceries", amount=Decimal("10.00"), payment_method="cash")
    add_expense(db, paid_date=date(2025, 1, 20), category="groceries", amount=Decimal("5.50"), payment_method="cash")
    add_expense(db, paid_date=date(2025, 2, 10), category="wi-fi", amount=Decimal("30.00"), payment_method="cash")
    add_expense(db, paid_date=date(2024, 12, 15), category="groceries", amount=Decimal("7.25"), payment_method="cash")


def test_period_total_sums_all_categories_in_period(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    seed(db)
    assert period_total(db, "2025-Q1") == Decimal("45.50")
    assert period_total(db, "2025-01") == Decimal("15.50")
    assert period_total(db, "2024") == Decimal("7.25")
    assert period_total(db, "2025-03") == Decimal("0.00")


def test_period_total_supports_paid_date_basis(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    seed(db)
    add_expense(
        db,
        paid_date=date(2025, 1, 5),
        category="electricity",
        amount=Decimal("9.00"),
        payment_method="cash",
        cost_month=date(2024, 12, 1),
        quantity=Decimal("10"),
    )
    assert period_total(db, "2025-01", basis="paid_date") == Decimal("24.50")
    assert period_total(db, "2025-01") == Decimal("15.50")


def test_report_cli_shows_grand_total_for_each_period_shape(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    seed(db)
    db.close()

    assert main(["report", "2025-Q1"]) == 0
    assert "Total: 45.50" in capsys.readouterr().out
    assert main(["report", "2025-01"]) == 0
    assert "Total: 15.50" in capsys.readouterr().out
    assert main(["report", "2025"]) == 0
    assert "Total: 45.50" in capsys.readouterr().out
    assert main(["report", "2024-06"]) == 0
    assert "Total: 0.00" in capsys.readouterr().out
