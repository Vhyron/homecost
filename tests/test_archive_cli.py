from decimal import Decimal

import duckdb
import pytest

from homecost.cli import main
from homecost.service import add_expense, archive_managed_value, today_in_timezone


def test_remove_command_confirms_archive_and_reports_count(tmp_path, monkeypatch, capsys):
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

    assert main(["categories", "remove", "groceries"]) == 0
    assert "1 expenses" in capsys.readouterr().out
    db = duckdb.connect(str(db_path), read_only=True)
    assert db.execute("SELECT category FROM expenses").fetchone() == ("groceries",)
    assert db.execute("SELECT is_active FROM categories WHERE name='groceries'").fetchone() == (False,)


def test_remove_cancellation_does_not_create_or_change_database(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("builtins.input", lambda prompt: "no")

    assert main(["categories", "remove", "groceries"]) == 0
    assert not (tmp_path / ".homecost" / "homecost.duckdb").exists()


def test_remove_commands_archive_vendors_and_payment_methods(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    from homecost.service import add_payment_method, add_vendor
    add_vendor(db, "market")
    add_payment_method(db, "wallet")
    db.close()
    monkeypatch.setattr("builtins.input", lambda prompt: "yes")

    assert main(["vendors", "remove", "market"]) == 0
    assert main(["payment-methods", "remove", "wallet"]) == 0
    db = duckdb.connect(str(db_path), read_only=True)
    assert db.execute("SELECT is_active FROM vendors WHERE name='market'").fetchone() == (False,)
    assert db.execute("SELECT is_active FROM payment_methods WHERE name='wallet'").fetchone() == (False,)


def test_csv_import_rejects_archived_category(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    archive_managed_value(db, "category", "groceries")
    db.close()
    db = duckdb.connect(str(db_path))
    today = today_in_timezone(db)
    db.close()
    csv_path = tmp_path / "archived.csv"
    csv_path.write_text(
        "paid_date,amount,category,payment_method\n"
        f"{today.isoformat()},1.00,groceries,cash\n"
    )

    with pytest.raises(SystemExit) as error:
        main(["import", str(csv_path)])
    assert error.value.code == 2
    assert "not active" in capsys.readouterr().err
    db = duckdb.connect(str(db_path), read_only=True)
    assert db.execute("SELECT count(*) FROM expenses").fetchone() == (0,)
