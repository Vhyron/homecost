from datetime import datetime
from zoneinfo import ZoneInfo

import duckdb

from homecost.cli import main


def test_import_accepts_bom_flexible_columns_blank_lines_and_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    paid_date = datetime.now(ZoneInfo("Asia/Manila")).date().isoformat()
    csv_path = tmp_path / "expenses.csv"
    csv_path.write_text(
        f"\ufeffvendor,amount,paid_date\n\n,{1.25},{paid_date}\n",
        encoding="utf-8",
    )
    assert main(["import", str(csv_path)]) == 0
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT paid_date, category, payment_method, vendor FROM expenses").fetchone() == (
        datetime.now(ZoneInfo("Asia/Manila")).date(), "unassigned", "unassigned", None
    )


def test_import_requires_paid_date_and_amount_headers(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("category,amount\ngroceries,1.00\n")
    try:
        main(["import", str(csv_path)])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("missing required header should fail")
    assert "paid_date" in capsys.readouterr().err


def test_import_rejects_unknown_managed_values_with_row_context(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    paid_date = datetime.now(ZoneInfo("Asia/Manila")).date().isoformat()
    csv_path = tmp_path / "unknown.csv"
    csv_path.write_text(
        "paid_date,amount,category,vendor,payment_method\n"
        f"{paid_date},1.00,unknown-category,,cash\n"
        f"{paid_date},1.00,groceries,unknown-vendor,cash\n"
        f"{paid_date},1.00,groceries,,unknown-method\n"
    )
    try:
        main(["import", str(csv_path)])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("unknown managed values should fail")
    error = capsys.readouterr().err
    assert "unknown-category" in error
    assert "unknown-vendor" in error
    assert "unknown-method" in error
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT count(*) FROM information_schema.tables WHERE table_name='expenses'").fetchone() == (0,)
