from datetime import date
from decimal import Decimal

import duckdb

from homecost.cli import main
from homecost.service import add_expense, bill_status


def test_bill_status_uses_cost_month_and_status_rules(tmp_path, monkeypatch):
    import homecost.service as service

    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    monkeypatch.setattr(service, "today_in_timezone", lambda db: date(2025, 3, 15))
    # February electricity recorded; wi-fi missing; January both recorded.
    add_expense(db, paid_date=date(2025, 2, 10), category="electricity", amount=Decimal("1.00"), payment_method="cash", cost_month=date(2025, 2, 1), quantity=Decimal("1"))
    add_expense(db, paid_date=date(2025, 1, 10), category="electricity", amount=Decimal("1.00"), payment_method="cash", cost_month=date(2025, 1, 1), quantity=Decimal("1"))
    add_expense(db, paid_date=date(2025, 1, 10), category="wi-fi", amount=Decimal("1.00"), payment_method="cash", cost_month=date(2025, 1, 1))

    assert bill_status(db, "2025-Q1") == [
        (date(2025, 1, 1), "electricity", "recorded"),
        (date(2025, 1, 1), "water", "missing"),
        (date(2025, 1, 1), "wi-fi", "recorded"),
        (date(2025, 2, 1), "electricity", "recorded"),
        (date(2025, 2, 1), "water", "missing"),
        (date(2025, 2, 1), "wi-fi", "missing"),
        (date(2025, 3, 1), "electricity", "pending"),
        (date(2025, 3, 1), "water", "pending"),
        (date(2025, 3, 1), "wi-fi", "pending"),
    ]


def test_bill_status_excludes_future_months_and_non_bill_categories(tmp_path, monkeypatch):
    import homecost.service as service

    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    monkeypatch.setattr(service, "today_in_timezone", lambda db: date(2025, 3, 15))
    expected = [
        (date(2025, month, 1), category, "pending" if month == 3 else "missing")
        for month in (1, 2, 3)
        for category in ("electricity", "water", "wi-fi")
    ]
    assert bill_status(db, "2025") == expected


def test_report_cli_shows_bill_status(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    add_expense(db, paid_date=date(2025, 1, 10), category="electricity", amount=Decimal("1.00"), payment_method="cash", cost_month=date(2025, 1, 1), quantity=Decimal("1"))
    db.close()

    assert main(["report", "2025-01"]) == 0
    assert "electricity bill: recorded" in capsys.readouterr().out.lower()
