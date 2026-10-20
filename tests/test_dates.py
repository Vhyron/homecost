from datetime import date, datetime as RealDateTime
from decimal import Decimal

import duckdb
import pytest

import homecost.service as service
from homecost.db import initialize


def add(db, paid_date, cost_month=None):
    return service.add_expense(
        db,
        paid_date=paid_date,
        category="groceries",
        amount=Decimal("1.00"),
        payment_method="cash",
        cost_month=cost_month,
    )


def test_today_uses_configured_household_timezone(tmp_path, monkeypatch):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    initialize(db)
    service.set_setting(db, "timezone", "UTC", confirm_timezone=True)

    class FrozenDateTime:
        @staticmethod
        def now(tz):
            assert tz.key == "UTC"
            return RealDateTime(2025, 1, 1, tzinfo=tz)

    monkeypatch.setattr(service, "datetime", FrozenDateTime)
    assert service.today_in_timezone(db) == date(2025, 1, 1)


def test_rejects_paid_date_after_household_today(tmp_path, monkeypatch):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    monkeypatch.setattr(service, "today_in_timezone", lambda db: date(2025, 1, 1), raising=False)
    with pytest.raises(ValueError, match="later than today"):
        add(db, date(2025, 1, 2))


def test_rejects_cost_month_gap_over_twelve_calendar_months(tmp_path, monkeypatch):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    monkeypatch.setattr(service, "today_in_timezone", lambda db: date(2025, 1, 1), raising=False)
    with pytest.raises(ValueError, match="12 calendar months"):
        add(db, date(2025, 1, 1), date(2023, 12, 1))


def test_accepts_twelve_month_gap_and_old_matching_dates(tmp_path, monkeypatch):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    monkeypatch.setattr(service, "today_in_timezone", lambda db: date(2025, 1, 1), raising=False)
    add(db, date(2025, 1, 1), date(2024, 1, 15))
    add(db, date(2010, 2, 2))
    assert db.execute("SELECT count(*) FROM expenses").fetchone() == (2,)
