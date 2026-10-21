import duckdb

from homecost.cli import main


def test_payment_method_add_uses_service(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("builtins.input", lambda prompt: "  GCash ")

    assert main(["payment-methods", "add"]) == 0
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT name FROM payment_methods WHERE name='gcash'").fetchone() == ("gcash",)
