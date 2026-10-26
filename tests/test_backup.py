from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import duckdb
import pytest

from homecost.cli import main
from homecost.db import initialize
from homecost.service import add_expense, create_backup, today_in_timezone


def make_db(tmp_path):
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
    return db, db_path


def test_backup_creates_verified_timestamped_copy(tmp_path):
    db, db_path = make_db(tmp_path)
    backups = tmp_path / "backups"
    path = create_backup(db, db_path, backups)

    assert path.parent == backups
    assert path.name.startswith("homecost-")
    assert path.name.endswith(".duckdb")
    check = duckdb.connect(str(path), read_only=True)
    assert check.execute("SELECT count(*) FROM expenses").fetchone() == (1,)


def test_backup_suffix_prevents_same_second_collision(tmp_path):
    db, db_path = make_db(tmp_path)
    backups = tmp_path / "backups"
    first = create_backup(db, db_path, backups)
    second = create_backup(db, db_path, backups)
    assert first != second
    assert backups.exists()


def test_failed_verification_deletes_nothing(tmp_path, monkeypatch):
    db, db_path = make_db(tmp_path)
    backups = tmp_path / "backups"
    first = create_backup(db, db_path, backups)

    def broken_verify(path):
        raise RuntimeError("verification failed")

    monkeypatch.setattr("homecost.service._verify_backup", broken_verify)
    with pytest.raises(RuntimeError):
        create_backup(db, db_path, backups)
    names = {path.name for path in backups.iterdir()}
    assert names == {first.name}


def test_backup_rotation_keeps_newest_configured_count(tmp_path):
    db, db_path = make_db(tmp_path)
    backups = tmp_path / "backups"
    oldest = create_backup(db, db_path, backups)
    middle = create_backup(db, db_path, backups)
    create_backup(db, db_path, backups, retention=2)
    names = sorted(path.name for path in backups.iterdir())
    assert oldest.name not in names
    assert len(names) == 2


def test_backup_cli_uses_backup_retention_setting(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    initialize(db)
    db.close()

    assert main(["backup"]) == 0
    output = capsys.readouterr().out
    assert "backup" in output.lower()
    backups = tmp_path / ".homecost" / "backups"
    assert len(list(backups.iterdir())) == 1
