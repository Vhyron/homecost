import duckdb
import pytest

from homecost.db import initialize
from homecost.service import add_vendor


def test_add_vendor_normalizes_name(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    initialize(db)
    add_vendor(db, "  Fresh   Market ")
    assert db.execute("SELECT name FROM vendors WHERE name='fresh market'").fetchone() == ("fresh market",)


def test_add_vendor_rejects_normalized_duplicate(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    initialize(db)
    add_vendor(db, " Shop  ")
    with pytest.raises(ValueError, match="already exists"):
        add_vendor(db, "SHOP")
