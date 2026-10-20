import duckdb
import pytest

from homecost.db import initialize
from homecost.service import add_payment_method


def test_add_payment_method_normalizes_name(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    initialize(db)
    add_payment_method(db, "  Pay   Pal ")
    assert db.execute("SELECT name FROM payment_methods WHERE name='pay pal'").fetchone() == ('pay pal',)


def test_add_payment_method_rejects_normalized_duplicate(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    initialize(db)
    with pytest.raises(ValueError, match="already exists"):
        add_payment_method(db, " CASH ")
