from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb

from homecost.cli import main


def test_import_reports_every_invalid_line_and_writes_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    tomorrow = (datetime.now(ZoneInfo("Asia/Manila")).date() + timedelta(days=1)).isoformat()
    csv_path = tmp_path / "expenses.csv"
    csv_path.write_text(
        f"paid_date,amount,category,payment_method\n{tomorrow},1.00,groceries,cash\n"
        "2025-01-01,0,groceries,cash\n"
        "2025-01-01,NaN,groceries,cash\n"
        "2025-01-01,2.00,groceries,cash\n"
    )

    try:
        main(["import", str(csv_path)])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("invalid file should fail")
    error = capsys.readouterr().err
    assert "line 2" in error
    assert "line 3" in error
    assert "line 4" in error

    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db = duckdb.connect(str(db_path), read_only=True)
    assert db.execute("SELECT count(*) FROM information_schema.tables WHERE table_name='expenses'").fetchone() == (0,)


def test_import_writes_all_valid_rows(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    csv_path = tmp_path / "expenses.csv"
    csv_path.write_text(
        "paid_date,amount,category,payment_method\n"
        "2025-01-01,1.00,groceries,cash\n"
        "2025-01-02,2.00,groceries,cash\n"
    )
    assert main(["import", str(csv_path)]) == 0
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT count(*) FROM expenses").fetchone() == (2,)
