from datetime import date
from decimal import Decimal

import duckdb

from homecost.cli import main
from homecost.service import add_expense


def test_report_cli_supports_cost_month_and_paid_date_bases(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    add_expense(
        db,
        paid_date=date(2025, 1, 5),
        category="electricity",
        amount=Decimal("9.00"),
        payment_method="cash",
        cost_month=date(2024, 12, 1),
        quantity=Decimal("10"),
    )
    db.close()

    assert main(["report", "2024-12", "--basis", "cost_month"]) == 0
    assert "9.00" in capsys.readouterr().out
    assert main(["report", "2024-12", "--basis", "paid_date"]) == 0
    assert "no expenses" in capsys.readouterr().out.lower()
