from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import duckdb

from homecost.cli import main


class Answers:
    """Map input prompts to queued answers by substring; record prompt order."""

    def __init__(self, mapping):
        self.mapping = {key: list(value) for key, value in mapping.items()}
        self.prompts = []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        for key, queue in self.mapping.items():
            if key in prompt and queue:
                value = queue.pop(0)
                if value == "^C":
                    raise KeyboardInterrupt
                return value
        raise AssertionError(f"unexpected prompt: {prompt}")


def today():
    return datetime.now(ZoneInfo("Asia/Manila")).date()


BASE_ANSWERS = {
    "Paid date": None,
    "Amount": None,
    "Category number": ["2"],
    "Payment method number": ["1"],
    "Vendor number": [""],
    "Cost month": [""],
    "Bill date": [""],
    "Quantity": None,
}


def metered_answers(paid=None, quantity="5.25", amount="123.45", overrides=None):
    mapping = dict(BASE_ANSWERS)
    mapping["Paid date"] = [paid or today().isoformat()]
    mapping["Quantity"] = [quantity]
    mapping["Amount"] = [amount]
    if overrides:
        mapping.update(overrides)
    return Answers(mapping)


def test_guided_add_uses_service_and_stores_metered_expense(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    answers = metered_answers()
    monkeypatch.setattr("builtins.input", answers)

    assert main(["add"]) == 0
    output = capsys.readouterr().out.lower()
    assert "electricity" in output
    assert "cash" in output

    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute(
        "SELECT paid_date, category, amount, cost_month, bill_date, payment_method, vendor, quantity FROM expenses"
    ).fetchone() == (
        today(), "electricity", Decimal("123.45"), today().replace(day=1), None, "cash", None, Decimal("5.250")
    )


def test_guided_add_prompts_in_specified_order(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    answers = metered_answers()
    monkeypatch.setattr("builtins.input", answers)

    assert main(["add"]) == 0
    order = []
    for prompt in answers.prompts:
        for key in ("Paid date", "Amount", "Category number", "Payment method number", "Vendor number",
                    "Cost month", "Bill date", "Quantity"):
            if key in prompt and key not in order:
                order.append(key)
    assert order == ["Paid date", "Amount", "Category number", "Payment method number", "Vendor number",
                     "Cost month", "Bill date", "Quantity"]


def test_guided_add_rejects_invalid_and_out_of_range_choice_numbers(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    answers = metered_answers(overrides={"Category number": ["0", "99", "3"], "Amount": ["2.00"]})
    monkeypatch.setattr("builtins.input", answers)

    assert main(["add"]) == 0
    output = capsys.readouterr().out
    assert "Enter a number between 1 and" in output
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT category FROM expenses").fetchone() == ("groceries",)


def test_guided_add_adds_new_category_in_category_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    answers = metered_answers(overrides={
        "Category number": ["10", "6"],
        "Category name": ["Home  Service "],
        "Unit (Enter": ["hours"],
        "Monthly bill": ["yes"],
        "Quantity": ["1.5"],
        "Amount": ["20.00"],
    })
    monkeypatch.setattr("builtins.input", answers)

    assert main(["add"]) == 0
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute(
        "SELECT name, unit, monthly_bill_expected FROM categories WHERE name='home service'"
    ).fetchone() == ("home service", "hours", True)
    assert db.execute("SELECT category, quantity FROM expenses").fetchone() == ("home service", Decimal("1.500"))


def test_guided_add_cost_month_accepts_YYYY_MM(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    answers = metered_answers(paid="2025-09-15", quantity="1", amount="10.00",
                              overrides={"Cost month": ["2025-09"]})
    monkeypatch.setattr("builtins.input", answers)

    assert main(["add"]) == 0
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT cost_month FROM expenses").fetchone() == (date(2025, 9, 1),)


def test_guided_add_can_add_and_select_existing_vendor(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".homecost" / "homecost.duckdb"

    answers = metered_answers(quantity=None, amount="3.50", overrides={
        "Category number": ["3"],
        "Vendor number": ["1"],
        "Vendor name": ["Corner Store"],
        "Quantity": [],
    })
    monkeypatch.setattr("builtins.input", answers)
    assert main(["add"]) == 0
    output = capsys.readouterr().out
    assert "add a vendor" in output
    assert "Add a vendor" not in output
    db = duckdb.connect(str(db_path), read_only=True)
    assert db.execute("SELECT vendor FROM expenses").fetchall() == [("corner store",)]
    db.close()

    answers = metered_answers(quantity=None, amount="4.00", overrides={
        "Category number": ["3"],
        "Vendor number": ["1"],
        "Quantity": [],
    })
    monkeypatch.setattr("builtins.input", answers)
    assert main(["add"]) == 0
    db = duckdb.connect(str(db_path), read_only=True)
    assert db.execute("SELECT vendor FROM expenses ORDER BY id").fetchall() == [
        ("corner store",), ("corner store",)
    ]


def test_guided_add_reprompts_on_invalid_paid_date(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    answers = metered_answers(paid="oops", overrides={"Paid date": ["oops", ""]})
    answers.mapping["Paid date"] = ["oops", today().isoformat()]
    monkeypatch.setattr("builtins.input", answers)

    assert main(["add"]) == 0
    assert "Enter the paid date as YYYY-MM-DD" in capsys.readouterr().out
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT count(*) FROM expenses").fetchone() == (1,)


def test_guided_add_reprompts_on_invalid_amount(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    answers = metered_answers(overrides={"Amount": ["", "abc", "-1", "10.50"]})
    monkeypatch.setattr("builtins.input", answers)

    assert main(["add"]) == 0
    output = capsys.readouterr().out
    assert "This field is required." in output
    assert "Enter a positive amount with at most two decimal places" in output
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT amount FROM expenses").fetchone() == (Decimal("10.50"),)


def test_guided_add_reprompts_on_invalid_cost_month(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    answers = metered_answers(paid="2025-09-15", overrides={"Cost month": ["2025-9", "2025-09"]})
    monkeypatch.setattr("builtins.input", answers)

    assert main(["add"]) == 0
    assert "Enter the cost month as YYYY-MM" in capsys.readouterr().out
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT cost_month FROM expenses").fetchone() == (date(2025, 9, 1),)


def test_guided_add_reprompts_on_invalid_bill_date(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    answers = metered_answers(overrides={"Bill date": ["junk", "2025-10-01"]})
    monkeypatch.setattr("builtins.input", answers)

    assert main(["add"]) == 0
    assert "Enter the bill date as YYYY-MM-DD" in capsys.readouterr().out
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT bill_date FROM expenses").fetchone() == (date(2025, 10, 1),)


def test_guided_add_reprompts_on_invalid_quantity(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    answers = metered_answers(overrides={"Quantity": ["", "1.2345", "5"]})
    monkeypatch.setattr("builtins.input", answers)

    assert main(["add"]) == 0
    output = capsys.readouterr().out
    assert "This field is required." in output
    assert "Enter a positive quantity with at most three decimal places" in output
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT quantity FROM expenses").fetchone() == (Decimal("5.000"),)


def test_guided_add_adds_new_payment_method_in_payment_method_prompt(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    answers = metered_answers(overrides={
        "Payment method number": ["2", "2"],
        "Payment method name": ["  GCash "],
    })
    monkeypatch.setattr("builtins.input", answers)

    assert main(["add"]) == 0
    output = capsys.readouterr().out
    assert "add a new payment method" in output
    assert "Added payment method gcash." in output
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT payment_method FROM expenses").fetchone() == ("gcash",)
    assert db.execute("SELECT count(*) FROM payment_methods WHERE name='gcash'").fetchone() == (1,)


def test_guided_add_ctrl_c_cancels_and_writes_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    answers = metered_answers(overrides={
        "Category number": ["10"],
        "Category name": ["Home Service"],
        "Unit (Enter": ["hours"],
        "Monthly bill": ["yes"],
    })
    answers.mapping["Category number"].append("^C")
    monkeypatch.setattr("builtins.input", answers)

    assert main(["add"]) == 0
    assert "canceled" in capsys.readouterr().out.lower()
    db = duckdb.connect(str(tmp_path / ".homecost" / "homecost.duckdb"), read_only=True)
    assert db.execute("SELECT count(*) FROM expenses").fetchone() == (0,)
    assert db.execute("SELECT count(*) FROM categories WHERE name='home service'").fetchone() == (0,)
