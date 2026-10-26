from datetime import date
from decimal import Decimal

import duckdb

from homecost.cli import main
from homecost.service import add_expense


def test_report_shows_grocery_trip_count_and_average(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    add_expense(db, paid_date=date(2025, 1, 5), category="groceries", amount=Decimal("10.00"), payment_method="cash")
    add_expense(db, paid_date=date(2025, 1, 20), category="groceries", amount=Decimal("5.50"), payment_method="cash")
    add_expense(db, paid_date=date(2025, 1, 21), category="wi-fi", amount=Decimal("30.00"), payment_method="cash")
    db.close()

    assert main(["report", "2025-01"]) == 0
    output = capsys.readouterr().out
    assert "trips: 2" in output
    assert "average: 7.75" in output


def test_report_omits_grocery_detail_when_no_grocery_expenses(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    add_expense(db, paid_date=date(2025, 1, 21), category="wi-fi", amount=Decimal("30.00"), payment_method="cash")
    db.close()

    assert main(["report", "2025-01"]) == 0
    assert "trips:" not in capsys.readouterr().out
