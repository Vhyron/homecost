import duckdb

from homecost.db import initialize


def test_installation_currency_defaults_to_php_and_is_not_per_expense(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    initialize(db)
    assert db.execute("SELECT value FROM settings WHERE key='currency'").fetchone() == ("PHP",)
    columns = {row[1] for row in db.execute("PRAGMA table_info('expenses')").fetchall()}
    assert "currency" not in columns
    assert "exchange_rate" not in columns
