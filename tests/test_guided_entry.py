from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import duckdb

from homecost.cli import main


def test_guided_add_uses_service_and_stores_metered_expense(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    today = datetime.now(ZoneInfo("Asia/Manila")).date()
    answers = iter([today.isoformat(), "2", "123.45", "1", "", "", "", "5.25"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    assert main(["add"]) == 0
    output = capsys.readouterr().out.lower()
    assert "electricity" in output
    assert "cash" in output

    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute(
        "SELECT paid_date, category, amount, cost_month, bill_date, payment_method, vendor, quantity FROM expenses"
    ).fetchone() == (
        today, "electricity", Decimal("123.45"), today.replace(day=1), None, "cash", None, Decimal("5.250")
    )


def test_guided_add_can_add_and_select_existing_vendor(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    today = datetime.now(ZoneInfo("Asia/Manila")).date()
    db_path = tmp_path / ".homecost" / "homecost.duckdb"

    add_vendor_answers = iter([today.isoformat(), "3", "3.50", "1", "1", "Corner Store", "", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(add_vendor_answers))
    assert main(["add"]) == 0

    select_vendor_answers = iter([today.isoformat(), "3", "4.00", "1", "1", "", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(select_vendor_answers))
    assert main(["add"]) == 0

    db = duckdb.connect(str(db_path), read_only=True)
    assert db.execute("SELECT vendor FROM expenses ORDER BY id").fetchall() == [
        ("corner store",), ("corner store",)
    ]
