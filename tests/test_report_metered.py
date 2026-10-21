from datetime import date
from decimal import Decimal

import duckdb

from homecost.cli import main
from homecost.service import add_expense, metered_summary


def seed(db):
    add_expense(db, paid_date=date(2025, 1, 15), category="electricity", amount=Decimal("100.00"), payment_method="cash", quantity=Decimal("100"))
    add_expense(db, paid_date=date(2025, 2, 15), category="electricity", amount=Decimal("130.00"), payment_method="cash", quantity=Decimal("120"))


def test_metered_summary_reports_totals_and_changes(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    seed(db)
    summary = metered_summary(db, "2025-02")
    assert summary == [("electricity", Decimal("130.00"), Decimal("120"), Decimal("1.08"), Decimal("20.00"), Decimal("0.08"))]


def test_metered_summary_reports_unavailable_comparison(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    seed(db)
    summary = metered_summary(db, "2025-01")
    assert summary == [("electricity", Decimal("100.00"), Decimal("100"), Decimal("1.00"), None, None)]


def test_report_cli_shows_metered_summary(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    seed(db)
    db.close()

    assert main(["report", "2025-02"]) == 0
    output = capsys.readouterr().out
    assert "electricity" in output
    assert "120.000" in output
    assert "1.08" in output
    assert "+20.00" in output and "+0.08" in output

    assert main(["report", "2025-01"]) == 0
    assert "Comparison unavailable: no usage was recorded for 2024-12." in capsys.readouterr().out


def test_report_cli_skips_metered_section_for_non_month_periods(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    seed(db)
    db.close()

    assert main(["report", "2025-Q1"]) == 0
    assert "Comparison unavailable" not in capsys.readouterr().out
