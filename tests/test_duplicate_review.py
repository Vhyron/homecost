from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import duckdb

from homecost.cli import main
from homecost.service import add_expense


def test_manual_entry_warns_and_can_skip_exact_match(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    today = datetime.now(ZoneInfo("Asia/Manila")).date()
    existing_id = add_expense(
        db,
        paid_date=today,
        category="groceries",
        amount=Decimal("10.00"),
        payment_method="cash",
    )
    db.close()
    answers = iter([today.isoformat(), "10.00", "3", "1", "", "", "", "no"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    assert main(["add"]) == 0
    output = capsys.readouterr().out
    assert str(existing_id) in output
    assert "10.00" in output
    db = duckdb.connect(str(db_path), read_only=True)
    assert db.execute("SELECT count(*) FROM expenses").fetchone() == (1,)


def test_manual_entry_can_confirm_adding_duplicate(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    today = datetime.now(ZoneInfo("Asia/Manila")).date()
    add_expense(
        db,
        paid_date=today,
        category="groceries",
        amount=Decimal("10.00"),
        payment_method="cash",
    )
    db.close()
    answers = iter([today.isoformat(), "10.00", "3", "1", "", "", "", "yes"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    assert main(["add"]) == 0
    db = duckdb.connect(str(db_path), read_only=True)
    assert db.execute("SELECT count(*) FROM expenses").fetchone() == (2,)


def test_csv_import_reviews_duplicate_in_saved_expenses(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    today = datetime.now(ZoneInfo("Asia/Manila")).date()
    add_expense(
        db,
        paid_date=today,
        category="groceries",
        amount=Decimal("10.00"),
        payment_method="cash",
    )
    db.close()
    csv_path = tmp_path / "duplicate.csv"
    csv_path.write_text(
        "paid_date,amount,category,payment_method\n"
        f"{today.isoformat()},10.00,groceries,cash\n"
    )
    monkeypatch.setattr("builtins.input", lambda prompt: "no")

    assert main(["import", str(csv_path)]) == 0
    assert "skipped 1" in capsys.readouterr().out.lower()
    db = duckdb.connect(str(db_path), read_only=True)
    assert db.execute("SELECT count(*) FROM expenses").fetchone() == (1,)


def test_csv_import_reviews_duplicate_rows_in_same_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    paid_date = datetime.now(ZoneInfo("Asia/Manila")).date().isoformat()
    csv_path = tmp_path / "duplicates.csv"
    csv_path.write_text(
        "paid_date,amount,category,payment_method\n"
        f"{paid_date},10.00,groceries,cash\n"
        f"{paid_date},10.00, Groceries , CASH \n"
    )
    answers = iter(["no"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    assert main(["import", str(csv_path)]) == 0
    output = capsys.readouterr().out.lower()
    assert "imported 1" in output
    assert "skipped 1" in output
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT count(*) FROM expenses").fetchone() == (1,)
