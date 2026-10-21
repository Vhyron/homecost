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


def test_list_cli_shows_aligned_table_with_blank_vendor(tmp_path, monkeypatch, capsys):
    from homecost.db import initialize
    from homecost.service import add_vendor

    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    initialize(db)
    add_vendor(db, "market")
    with_vendor = create(db, "groceries", "cash")
    add_expense(
        db,
        paid_date=today_in_timezone(db),
        category="wi-fi",
        amount=Decimal("30.00"),
        payment_method="cash",
    )
    no_vendor = with_vendor + 1
    db.close()

    assert main(["list"]) == 0
    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert any("vendor" in line.lower() for line in lines[:1])
    rows = [line for line in lines if line.split()[0] in {str(with_vendor), str(no_vendor)}]
    assert len(rows) == 2
    assert not any("-" == cell for row in rows for cell in row.split())
    # The category column starts at the same offset in both rows (aligned table).
    category_positions = {row.index("groceries") for row in rows if "groceries" in row}
    wifi_positions = {row.index("wi-fi") for row in rows if "wi-fi" in row}
    assert len(category_positions | wifi_positions) == 1
