import duckdb

from homecost.cli import main


def test_category_add_requires_and_stores_monthly_bill_choice(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    answers = iter(["  Home   Service ", "hours", "yes"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    assert main(["categories", "add"]) == 0
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute(
        "SELECT name, unit, monthly_bill_expected FROM categories WHERE name='home service'"
    ).fetchone() == ("home service", "hours", True)


def test_category_add_rejects_non_yes_no_answer(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    answers = iter(["new category", "", "maybe"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    try:
        main(["categories", "add"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("invalid monthly-bill answer should fail")

    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT count(*) FROM information_schema.tables WHERE table_name='categories'").fetchone() == (0,)
