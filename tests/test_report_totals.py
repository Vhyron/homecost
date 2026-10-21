from datetime import date
from decimal import Decimal

import duckdb
import pytest

from homecost.service import add_expense, category_totals, month_detail
from homecost.cli import main


def seed(db):
    add_expense(db, paid_date=date(2025, 1, 5), category="groceries", amount=Decimal("10.00"), payment_method="cash")
    add_expense(db, paid_date=date(2025, 1, 20), category="groceries", amount=Decimal("5.50"), payment_method="cash")
    add_expense(db, paid_date=date(2025, 2, 10), category="wi-fi", amount=Decimal("30.00"), payment_method="cash")
    add_expense(db, paid_date=date(2024, 12, 15), category="groceries", amount=Decimal("7.25"), payment_method="cash")


def test_month_report_totals_by_category(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    seed(db)
    assert category_totals(db, "2025-01") == [("groceries", Decimal("15.50"))]


def test_quarter_report_totals_and_month_detail(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    seed(db)
    assert category_totals(db, "2025-Q1") == [("groceries", Decimal("15.50")), ("wi-fi", Decimal("30.00"))]
    assert month_detail(db, "2025-Q1") == [
        (date(2025, 1, 1), "groceries", Decimal("15.50")),
        (date(2025, 2, 1), "wi-fi", Decimal("30.00")),
    ]


def test_year_report_totals_exclude_other_years(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    seed(db)
    assert category_totals(db, "2024") == [("groceries", Decimal("7.25"))]
    assert category_totals(db, "2025") == [("groceries", Decimal("15.50")), ("wi-fi", Decimal("30.00"))]


def test_report_supports_paid_date_basis(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    seed(db)
    # January grocery expense assigned to December 2024 cost month.
    add_expense(
        db,
        paid_date=date(2025, 1, 5),
        category="electricity",
        amount=Decimal("9.00"),
        payment_method="cash",
        cost_month=date(2024, 12, 1),
        quantity=Decimal("10"),
    )
    assert category_totals(db, "2025-01", basis="paid_date") == [
        ("electricity", Decimal("9.00")),
        ("groceries", Decimal("15.50")),
    ]
    assert category_totals(db, "2025-01") == [("groceries", Decimal("15.50"))]


@pytest.mark.parametrize("period", ["2025-13", "2025-Q9", "2025-01-01", "bogus"])
def test_report_rejects_invalid_periods(tmp_path, period):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    with pytest.raises(ValueError):
        category_totals(db, period)


def test_report_cli_shows_totals_with_month_detail(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    seed(db)
    db.close()

    assert main(["report", "2025-Q1"]) == 0
    output = capsys.readouterr().out
    assert "groceries" in output
    assert "15.50" in output
    assert "wi-fi" in output
    assert "30.00" in output
    assert "2025-01" in output and "2025-02" in output
