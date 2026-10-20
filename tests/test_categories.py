import duckdb
import pytest

from homecost.db import initialize
from homecost.service import add_category


def test_add_category_normalizes_name(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    initialize(db)
    add_category(db, "  Home   foo ")
    assert db.execute("SELECT name FROM categories WHERE name='home foo'").fetchone() == ("home foo",)


def test_add_category_rejects_normalized_duplicate(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    initialize(db)
    with pytest.raises(ValueError, match="already exists"):
        add_category(db, "  ELECTRICITY  ")
