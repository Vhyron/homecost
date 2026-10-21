from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

from homecost.cli import main
from homecost.db import initialize
from homecost.service import add_expense, create_backup, restore_backup, today_in_timezone


def make_db_with_backup(tmp_path):
    db_path = tmp_path / "homecost.duckdb"
    db = duckdb.connect(str(db_path))
    initialize(db)
    add_expense(
        db,
        paid_date=today_in_timezone(db),
        category="groceries",
        amount=Decimal("1.00"),
        payment_method="cash",
    )
    backup = create_backup(db, db_path, tmp_path / "backups")
    db.close()
    return backup


def test_restore_copies_backup_to_new_database(tmp_path):
    backup = make_db_with_backup(tmp_path)
    target = tmp_path / "restored.duckdb"

    restore_backup(backup, target)

    restored = duckdb.connect(str(target), read_only=True)
    assert restored.execute("SELECT count(*) FROM expenses").fetchone() == (1,)


def test_restore_refuses_to_overwrite_existing_database(tmp_path):
    backup = make_db_with_backup(tmp_path)
    target = tmp_path / "existing.duckdb"
    target.write_bytes(b"existing")

    with pytest.raises(ValueError, match="already exists"):
        restore_backup(backup, target)
    assert target.read_bytes() == b"existing"


def test_restore_cli_restores_to_new_path(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    backup = make_db_with_backup(tmp_path)
    target = tmp_path / "restored-cli.duckdb"

    assert main(["restore", str(backup), "--to", str(target)]) == 0
    assert "restored" in capsys.readouterr().out.lower()
    restored = duckdb.connect(str(target), read_only=True)
    assert restored.execute("SELECT count(*) FROM expenses").fetchone() == (1,)
