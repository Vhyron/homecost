import duckdb

from homecost.cli import main
from homecost.service import add_payment_method, add_vendor, archive_managed_value


def test_list_commands_show_active_and_archived_values(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    add_vendor(db, "market")
    archive_managed_value(db, "category", "groceries")
    archive_managed_value(db, "vendor", "market")
    add_payment_method(db, "wallet")
    archive_managed_value(db, "payment_method", "wallet")
    db.close()

    assert main(["categories", "list"]) == 0
    assert main(["vendors", "list"]) == 0
    assert main(["payment-methods", "list"]) == 0
    output = capsys.readouterr().out
    assert "groceries (archived)" in output
    assert "electricity (active)" in output
    assert "market (archived)" in output
    assert "wallet (archived)" in output


def test_vendors_add_reactivates_archived_value(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    add_vendor(db, "market")
    archive_managed_value(db, "vendor", "market")
    db.close()
    monkeypatch.setattr("builtins.input", lambda prompt: " Market ")

    assert main(["vendors", "add"]) == 0
    db = duckdb.connect(str(db_path), read_only=True)
    assert db.execute("SELECT count(*) FROM vendors WHERE name='market'").fetchone() == (1,)
    assert db.execute("SELECT is_active FROM vendors WHERE name='market'").fetchone() == (True,)
