from datetime import datetime
from zoneinfo import ZoneInfo

import duckdb

from homecost.cli import main
from homecost.service import today_in_timezone


def test_report_labels_current_period_to_date(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"
    db_path.parent.mkdir(parents=True)
    db = duckdb.connect(str(db_path))
    today = today_in_timezone(db)
    db.close()

    current_month = f"{today.year}-{today.month:02d}"
    quarter = (today.month - 1) // 3 + 1
    current_quarter = f"{today.year}-Q{quarter}"
    past_month = "2001-01"

    assert main(["report", current_month]) == 0
    assert "to date" in capsys.readouterr().out.lower()
    assert main(["report", current_quarter]) == 0
    assert "to date" in capsys.readouterr().out.lower()
    assert main(["report", str(today.year)]) == 0
    assert "to date" in capsys.readouterr().out.lower()
    assert main(["report", past_month]) == 0
    assert "to date" not in capsys.readouterr().out.lower()
