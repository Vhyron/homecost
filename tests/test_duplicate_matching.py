from datetime import date
from decimal import Decimal

import duckdb
import pytest

from homecost.service import add_expense, find_duplicate, same_expense, today_in_timezone


def base_fields(db):
    today = today_in_timezone(db)
    return {
        "paid_date": today,
        "category": "groceries",
        "amount": Decimal("1.25"),
        "payment_method": "cash",
        "vendor": None,
        "cost_month": None,
        "bill_date": None,
        "quantity": None,
    }


def test_duplicate_lookup_applies_defaults_and_name_normalization(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    fields = base_fields(db)
    expense_id = add_expense(db, **fields)
    candidate = {**fields, "category": "  GROCERIES ", "payment_method": " CASH "}
    assert find_duplicate(db, candidate) == expense_id


@pytest.mark.parametrize(
    "field,value",
    [
        ("paid_date", date(2024, 1, 1)),
        ("cost_month", date(2024, 1, 1)),
        ("bill_date", date(2024, 1, 1)),
        ("category", "electricity"),
        ("amount", Decimal("1.26")),
        ("vendor", "market"),
        ("quantity", Decimal("1")),
        ("payment_method", "unassigned"),
    ],
)
def test_duplicate_comparison_checks_each_specified_field(tmp_path, field, value):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    original = base_fields(db)
    changed = {**original, field: value}
    assert not same_expense(original, changed)
