from datetime import date
from decimal import Decimal

import duckdb
import pytest

from homecost.service import add_expense, delete_expense, today_in_timezone


def create(db, amount):
    return add_expense(
        db,
        paid_date=today_in_timezone(db),
        category="groceries",
        amount=Decimal(amount),
        payment_method="cash",
    )


def test_delete_permanently_removes_only_selected_expense(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    first = create(db, "1.00")
    second = create(db, "2.00")

    delete_expense(db, first)

    assert db.execute("SELECT id, amount FROM expenses").fetchall() == [(second, Decimal("2.00"))]


def test_delete_rejects_unknown_expense_id(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    with pytest.raises(ValueError, match="does not exist"):
        delete_expense(db, 12)


def test_delete_cli_confirms_and_removes_expense(tmp_path, monkeypatch):
    from homecost.cli import main

    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    expense_id = create(db, "1.00")
    db.close()

    monkeypatch.setattr("builtins.input", lambda prompt: "yes")
    assert main(["delete", str(expense_id)]) == 0
    db = duckdb.connect(str(db_path), read_only=True)
    assert db.execute("SELECT count(*) FROM expenses").fetchone() == (0,)


def test_delete_cli_requires_confirmation(tmp_path, monkeypatch, capsys):
    from homecost.cli import main

    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    expense_id = create(db, "1.00")
    db.close()

    monkeypatch.setattr("builtins.input", lambda prompt: "no")
    assert main(["delete", str(expense_id)]) == 0
    assert "cancel" in capsys.readouterr().out.lower()
    db = duckdb.connect(str(db_path), read_only=True)
    assert db.execute("SELECT count(*) FROM expenses").fetchone() == (1,)
