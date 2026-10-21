# CLI entry, managed lists, and CSV import

This is the normative home for I-01–I-09 and I-11–I-14. Requirement IDs remain stable for task and test references. Settings behavior is in [operations](operations.md).

## Command reference

| Command | Purpose |
|---|---|
| `homecost init` | Create the database and seed default categories and payment methods; vendors start empty. |
| `homecost add` | Guided entry for one expense. |
| `homecost import FILE.csv` | Import a CSV batch. |
| `homecost list [--category CATEGORY] [--payment-method METHOD]` | List expenses with their IDs; filter by category or payment method, including `unassigned`. |
| `homecost edit ID` / `homecost delete ID` | Correct or permanently remove one expense. |
| `homecost categories list`, `homecost categories add`, `homecost categories rename OLD NEW`, `homecost categories remove NAME` | List or manage categories. |
| `homecost vendors list`, `homecost vendors add`, `homecost vendors rename OLD NEW`, `homecost vendors remove NAME` | List or manage vendors. Vendors can also be added during guided entry. |
| `homecost payment-methods list`, `homecost payment-methods add`, `homecost payment-methods rename OLD NEW`, `homecost payment-methods remove NAME` | List or manage payment methods. |
| `homecost --help` | Show command help. |

## Entry and CSV requirements

| ID | Requirement |
|---|---|
| I-01 | CLI entry and CSV import use the same service validation. |
| I-02 | `homecost add` is guided entry for one expense. Show numbered choices for category and required payment method. Let the user choose an existing vendor, add one, or press Enter to leave vendor empty. Optional fields may be skipped; `cost_month` defaults to the paid month. Tests: `test_guided_add_uses_service_and_stores_metered_expense`, `test_guided_add_can_add_and_select_existing_vendor`. |
| I-03 | `homecost categories add` creates a category with a name, optional unit, and requires an explicit yes/no answer for monthly-bill-expected; there is no default. Tests: `test_category_add_requires_and_stores_monthly_bill_choice`, `test_category_add_rejects_non_yes_no_answer`. |
| I-04 | Validate the full CSV before writing. If any row is invalid, import nothing and report every problem with its file line number. After duplicate review, import all accepted rows together. Accept a UTF-8 BOM and blank lines. |
| I-05 | A CSV header is required; column order is flexible. Required columns: `paid_date`, `amount`. Optional columns: `category`, `vendor`, `cost_month`, `bill_date`, `quantity`, `payment_method`. All amounts use the installation currency. If the category or payment-method column is absent or its value is blank, use the reserved `unassigned` value. A blank vendor stays empty. A nonblank category, vendor, or payment method not in its active managed list rejects the whole import with the row and value; tell the user to add/reactivate the list item or correct the CSV and retry. |
| I-06 | Editing an expense is atomic and applies the same validation as creation. Preserve its id and source. |
| I-07 | Deleting an expense requires CLI confirmation and permanently removes it. A backup is the recovery path; no audit log is required in v1. |
| I-08 | `homecost payment-methods add` adds a method to the managed list. Test: `test_payment_method_add_uses_service`. |
| I-09 | Use the same exact-match duplicate check for manual entry and CSV import. Compare `paid_date`, `cost_month`, `bill_date`, `category`, `amount`, `vendor`, `quantity`, and `payment_method` after defaults and normalization, against saved expenses and earlier rows in the same import. For manual entry, show the matching expense and ask whether to add anyway. For CSV import, pause for each matching row and let the user skip it or import it anyway; then import the accepted rows together and report what was imported or skipped. |
| I-11 | Renaming a category, vendor, or payment method changes its name on all existing expenses and for future entries. Confirm and report how many expenses are affected; reject normalized duplicates and reserved `unassigned`. |
| I-12 | Removing a category, vendor, or payment method requires confirmation and archives it rather than deleting it. Show how many existing expenses use it; those expenses and reports retain the value. Archived values are unavailable for new manual entries and CSV imports. The reserved `unassigned` values cannot be removed. |
| I-13 | `homecost list --category unassigned` and `homecost list --payment-method unassigned` find expenses with missing classifications. Editing one expense changes only that expense; it does not rename or remove the reserved `unassigned` values. |
| I-14 | Managed-list `list` commands show active and archived values. Adding a value that already exists as archived reactivates it instead of creating a duplicate. |