from datetime import date
from decimal import Decimal

import duckdb

from homecost.cli import main
from homecost.service import add_expense, today_in_timezone


def test_rename_cli_confirms_and_reports_affected_expenses(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    add_expense(
        db,
        paid_date=today_in_timezone(db),
        category="groceries",
        amount=Decimal("1.00"),
        payment_method="cash",
    )
    db.close()
    monkeypatch.setattr("builtins.input", lambda prompt: "yes")

    assert main(["categories", "rename", "groceries", "food"]) == 0
    assert "1" in capsys.readouterr().out
    db = duckdb.connect(str(db_path), read_only=True)
    assert db.execute("SELECT category FROM expenses").fetchone() == ("food",)
    assert db.execute("SELECT count(*) FROM categories WHERE name='food'").fetchone() == (1,)


def test_rename_vendor_and_payment_method_commands(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    from homecost.service import add_payment_method, add_vendor
    add_vendor(db, "market")
    add_payment_method(db, "wallet")
    db.close()
    monkeypatch.setattr("builtins.input", lambda prompt: "yes")

    assert main(["vendors", "rename", "market", "shop"]) == 0
    assert main(["payment-methods", "rename", "wallet", "card"]) == 0
    db = duckdb.connect(str(db_path), read_only=True)
    assert db.execute("SELECT name FROM vendors").fetchone() == ("shop",)
    assert db.execute("SELECT name FROM payment_methods WHERE name='card'").fetchone() == ("card",)


def test_rename_cli_cancellation_keeps_value(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("builtins.input", lambda prompt: "no")

    assert main(["categories", "rename", "groceries", "food"]) == 0
    assert not (tmp_path / ".homecost" / "homecost.duckdb").exists()
