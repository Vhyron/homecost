from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import duckdb

from homecost.cli import main


def _fails_with_validation_error(argv):
    try:
        main(argv)
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("invalid expense should be rejected")


def test_guided_entry_and_csv_import_share_service_validation(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    tomorrow = (datetime.now(ZoneInfo("Asia/Manila")).date() + timedelta(days=1)).isoformat()
    answers = iter([tomorrow, "1.00", "3", "1", "", "", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    _fails_with_validation_error(["add"])
    guided_error = capsys.readouterr().err

    csv_path = tmp_path / "future.csv"
    csv_path.write_text(
        f"paid_date,amount,category,payment_method\n{tomorrow},1.00,groceries,cash\n"
    )
    _fails_with_validation_error(["import", str(csv_path)])
    csv_error = capsys.readouterr().err

    message = "paid_date cannot be later than today in the household time zone"
    assert message in guided_error
    assert message in csv_error
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT count(*) FROM expenses").fetchone() == (0,)
