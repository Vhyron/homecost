import duckdb

from homecost.service import (
    add_category,
    add_payment_method,
    add_vendor,
    archive_managed_value,
    list_managed_values,
)


def test_adding_archived_values_reactivates_without_overwriting(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    archive_managed_value(db, "category", "electricity")
    add_vendor(db, "market")
    archive_managed_value(db, "vendor", "market")
    add_payment_method(db, "wallet")
    archive_managed_value(db, "payment_method", "wallet")

    add_category(db, "Electricity", "new unit", False)
    add_vendor(db, " MARKET ")
    add_payment_method(db, "WALLET")

    assert db.execute(
        "SELECT unit, monthly_bill_expected, is_active FROM categories WHERE name='electricity'"
    ).fetchone() == ("kWh", True, True)
    assert db.execute("SELECT count(*) FROM vendors WHERE name='market'").fetchone() == (1,)
    assert db.execute("SELECT is_active FROM vendors WHERE name='market'").fetchone() == (True,)
    assert db.execute("SELECT is_active FROM payment_methods WHERE name='wallet'").fetchone() == (True,)


def test_managed_lists_show_active_and_archived_values(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    archive_managed_value(db, "category", "groceries")
    assert ("groceries", "archived") in list_managed_values(db, "category")
    assert ("electricity", "active") in list_managed_values(db, "category")
