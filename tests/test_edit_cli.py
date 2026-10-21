from decimal import Decimal

import duckdb

from homecost.cli import main
from homecost.db import initialize
from homecost.service import add_expense, add_vendor, today_in_timezone


def test_edit_command_updates_amount_and_preserves_other_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    initialize(db)
    add_vendor(db, "market")
    today = today_in_timezone(db)
    expense_id = add_expense(
        db,
        paid_date=today,
        category="groceries",
        amount=Decimal("10.25"),
        payment_method="cash",
        vendor="market",
    )
    db.close()
    answers = iter(["", "", "12.00", "", "", "", "", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    assert main(["edit", str(expense_id)]) == 0

    db = duckdb.connect(str(db_path), read_only=True)
    row = db.execute("SELECT id, paid_date, category, amount, vendor, payment_method FROM expenses").fetchone()
    assert row == (expense_id, today, "groceries", Decimal("12.00"), "market", "cash")
