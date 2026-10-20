from homecost.cli import main


def test_settings_cli_shows_defaults_and_paths(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert main(["settings"]) == 0
    output = capsys.readouterr().out
    assert "timezone: Asia/Manila" in output
    assert f"database: {tmp_path}/.homecost/homecost.duckdb" in output
    assert f"backups: {tmp_path}/.homecost/backups" in output


def test_settings_cli_confirms_timezone_change(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("builtins.input", lambda _: "y")
    assert main(["settings", "set", "timezone", "UTC"]) == 0
