import duckdb

from homecost.db import initialize


def test_monthly_bill_eligibility_is_stored_on_categories(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    initialize(db)
    assert db.execute(
        "SELECT name, monthly_bill_expected FROM categories ORDER BY name"
    ).fetchall() == [
        ("drinking water", False),
        ("electricity", True),
        ("groceries", False),
        ("home appliances", False),
        ("home maintenance & repairs", False),
        ("home supplies", False),
        ("meals & snacks", False),
        ("unassigned", False),
        ("water", True),
        ("wi-fi", True),
    ]
