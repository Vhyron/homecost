import duckdb
import pytest

from homecost.db import initialize
from homecost.service import get_settings, set_setting


def test_settings_have_defaults(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    initialize(db)
    assert get_settings(db) == {"currency": "PHP", "timezone": "Asia/Manila", "backup-retention": "5"}


@pytest.mark.parametrize("key,value", [("unknown", "x"), ("timezone", "Not/AZone"), ("currency", "abc"), ("backup-retention", "0"), ("backup-retention", "1.5")])
def test_invalid_setting_is_rejected_without_change(tmp_path, key, value):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    initialize(db)
    old = get_settings(db)
    with pytest.raises(ValueError):
        set_setting(db, key, value, confirm_timezone=True)
    assert get_settings(db) == old


def test_currency_and_retention_settings_persist(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    initialize(db)
    set_setting(db, "currency", "usd")
    set_setting(db, "backup-retention", "10")
    assert get_settings(db)["currency"] == "USD"
    assert get_settings(db)["backup-retention"] == "10"


def test_timezone_change_requires_confirmation(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    initialize(db)
    with pytest.raises(ValueError, match="confirmation"):
        set_setting(db, "timezone", "UTC")
    set_setting(db, "timezone", "UTC", confirm_timezone=True)
    assert get_settings(db)["timezone"] == "UTC"


def test_currency_cannot_change_after_first_expense(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    initialize(db)
    db.execute("INSERT INTO expenses (paid_date, category, amount, cost_month, payment_method) VALUES ('2025-01-01', 'groceries', 1.00, '2025-01-01', 'cash')")
    with pytest.raises(ValueError, match="first expense"):
        set_setting(db, "currency", "USD")
    assert get_settings(db)["currency"] == "PHP"
