import duckdb

from homecost.db import initialize


def test_initialize_is_repeatable_and_adds_seeds_without_overwriting(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    initialize(db)
    db.execute("UPDATE categories SET unit = 'custom' WHERE name = 'electricity'")
    db.execute("INSERT INTO categories (name, unit) VALUES ('my category', NULL)")
    db.execute("INSERT INTO vendors (name) VALUES ('my vendor')")
    db.execute("INSERT INTO payment_methods (name) VALUES ('my method')")

    initialize(db)

    assert db.execute("SELECT unit FROM categories WHERE name='electricity'").fetchone() == ('custom',)
    assert db.execute("SELECT count(*) FROM categories WHERE name='my category'").fetchone() == (1,)
    assert db.execute("SELECT count(*) FROM vendors WHERE name='my vendor'").fetchone() == (1,)
    assert db.execute("SELECT count(*) FROM payment_methods WHERE name='my method'").fetchone() == (1,)
    assert db.execute("SELECT count(*) FROM categories WHERE name='groceries'").fetchone() == (1,)
    assert db.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall() == [(1,), (2,), (3,), (4,)]
