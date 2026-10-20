from pathlib import Path

import duckdb


_MIGRATIONS = Path(__file__).parent / "migrations"
_CATEGORIES = (
    ("electricity", "kWh", True),
    ("water", "m³", True),
    ("groceries", None, False),
    ("meals & snacks", None, False),
    ("drinking water", "gallons", False),
    ("home appliances", None, False),
    ("wi-fi", None, True),
    ("home supplies", None, False),
    ("home maintenance & repairs", None, False),
    ("unassigned", None, False),
)


def initialize(db: duckdb.DuckDBPyConnection) -> None:
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)")
    applied = {row[0] for row in db.execute("SELECT version FROM schema_migrations").fetchall()}
    for path in sorted(_MIGRATIONS.glob("[0-9]*_*.sql")):
        version = int(path.name.split("_", 1)[0])
        if version not in applied:
            db.execute(path.read_text())
            db.execute("INSERT INTO schema_migrations VALUES (?)", [version])

    db.executemany(
        "INSERT INTO categories (name, unit, monthly_bill_expected) VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
        _CATEGORIES,
    )
    db.executemany(
        "INSERT INTO payment_methods (name) VALUES (?) ON CONFLICT DO NOTHING",
        [("cash",), ("unassigned",)],
    )
