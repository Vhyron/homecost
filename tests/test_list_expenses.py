import duckdb

from decimal import Decimal

from homecost.cli import main
from homecost.service import add_expense, list_expenses, today_in_timezone


def create(db, category, payment_method):
    return add_expense(
        db,
        paid_date=today_in_timezone(db),
        category=category,
        amount=Decimal("1.00"),
        payment_method=payment_method,
    )


def test_list_expenses_filters_by_category_and_payment_method(tmp_path):
    db = duckdb.connect(str(tmp_path / "test.duckdb"))
    groceries_id = create(db, "groceries", "cash")
    unassigned_id = create(db, "unassigned", "unassigned")
    other_id = create(db, "wi-fi", "cash")

    assert [row[0] for row in list_expenses(db, category="unassigned")] == [unassigned_id]
    assert [row[0] for row in list_expenses(db, payment_method="unassigned")] == [unassigned_id]
    assert sorted(row[0] for row in list_expenses(db, category="groceries")) == [groceries_id]
    assert {row[0] for row in list_expenses(db)} == {groceries_id, unassigned_id, other_id}


def test_list_cli_shows_ids_and_filters_unassigned(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    unassigned_id = create(db, "unassigned", "unassigned")
    groceries_id = create(db, "groceries", "cash")
    db.close()

    assert main(["list", "--category", "unassigned"]) == 0
    assert str(unassigned_id) in capsys.readouterr().out
    assert main(["list", "--payment-method", "unassigned"]) == 0
    assert str(unassigned_id) in capsys.readouterr().out
    assert main(["list"]) == 0
    output = capsys.readouterr().out
    assert str(unassigned_id) in output
    assert str(groceries_id) in output
