# homecost

Homecost is a small household cost warehouse. It records expenses and reports spending by category for a month, quarter, or year, with month-by-month detail. Reports include both the month a cost belongs to and the date it was paid.

The first version is for one household per installation. It runs on a Mac and should be portable to a dedicated Raspberry Pi later. Expenses are entered through a CLI or imported from CSV. There is no API or front end in v1.

> **Current phase:** Phase 1 — implementation is in progress against the approved SPEC.

## What it tracks

Starter categories are lowercase defaults seeded at initialization: `electricity`, `water`, `groceries`, `meals & snacks`, `drinking water`, `home appliances`, `wi-fi`, `home supplies`, and `home maintenance & repairs`. Users can add categories during use; v1 does not replace the starter list before initialization. `groceries` is for grocery-shopping trips; `meals & snacks` is for ready-to-eat food bought separately, including dine-in, takeaway, delivery, and bakery food. Vendor/store is optional and selected from or added to a managed list; vendor names are also normalized to lowercase.

Electricity uses kWh, water uses m³, and drinking-water quantity is recorded in gallons (5 gallons per standard refill). Each grocery trip is one expense; grocery items are not tracked. Payment method is a separate managed list initialized with `cash` and reserved `unassigned`; the owner can add methods such as GCash, Maya, BPI, and PNB, which are stored in lowercase. CSV rows with blank category or payment method go to `unassigned` so they can be corrected later; unknown nonblank list values stop the import with an error rather than being silently changed.

## Expense dates

- `paid_date`: when the money left.
- `cost_month`: the month the owner assigns the cost to. It defaults to the paid month but can be set separately for a utility bill.
- `bill_date`: when a bill was issued. It does not determine the cost month.

For example, an October utility bill paid in November can count toward October. V1 does not split bills across months.

## Develop and test

Use `uv sync` to install the pinned dependencies and `uv run pytest` to run the test suite. The project uses Python 3.11+, `argparse`, and `pytest`.

## CLI overview

Planned command reference:

- `homecost init`; `homecost add`; `homecost import FILE.csv`
- `homecost list [--category CATEGORY] [--payment-method METHOD]`, `homecost edit ID`, `homecost delete ID`
- `homecost categories list`, `homecost categories add`, `homecost categories rename OLD NEW`, `homecost categories remove NAME`
- `homecost vendors list`, `homecost vendors add`, `homecost vendors rename OLD NEW`, `homecost vendors remove NAME`
- `homecost payment-methods list`, `homecost payment-methods add`, `homecost payment-methods rename OLD NEW`, `homecost payment-methods remove NAME`
- `homecost report PERIOD --basis BASIS`
- `homecost settings` and `homecost settings set KEY VALUE`
- `homecost backup`; `homecost restore BACKUP --to DATABASE`

`homecost add` guides you through one expense with numbered category and payment-method choices; press Enter to leave the optional vendor empty. Report periods are `YYYY-MM`, `YYYY-Qn`, or `YYYY`; basis is `cost_month` or `paid_date`. Renaming changes labels on past and future expenses; removing archives an item without changing past expenses. Use `homecost list --category unassigned` or `homecost list --payment-method unassigned` to find expenses needing classification, then edit the individual expense. `homecost add`, `homecost import FILE.csv`, `homecost list`, `homecost edit ID`, `homecost delete ID`, `homecost report PERIOD --basis BASIS`, `homecost backup`, `homecost restore BACKUP --to DATABASE`, `homecost categories list/add/rename/remove`, `homecost vendors list/add/rename/remove`, `homecost payment-methods list/add/rename/remove`, `homecost settings`, and `homecost settings set KEY VALUE` are implemented; other commands remain planned. `docs/SPEC.md` links to the command reference and focused requirements.

CSV import is for batches. Use a header with `paid_date` and `amount`; category, vendor, cost month, bill date, quantity, and payment method are optional columns. Blank category or payment method becomes `unassigned`; blank vendor stays empty. The importer validates the whole file first and reports all invalid rows without importing any. For each possible duplicate, it shows the match and asks whether to import anyway; the final message reports imported and skipped rows.

## Settings

Each installation's settings are managed with `homecost settings`; supported keys are `timezone`, `currency`, and `backup-retention`. Settings are stored in the database and included in backups. Currency cannot be changed after the first expense. The database defaults to `~/.homecost/homecost.duckdb`; local backups go in `~/.homecost/backups/` with timestamped filenames. Backup retention defaults to 5 (allowed range 1–365). Time zone defaults to `Asia/Manila` and currency to PHP. All expenses use the installation currency; convert foreign-currency amounts before entry.

## Project docs

- `docs/INDEX.md` — main map; read only the topics relevant to the task.
- `docs/SPEC.md` — index to the approved, topic-split behavior contract in `docs/spec/`.
- `docs/DECISIONS.md` — index to settled choices in `docs/decisions/`.
- `docs/DESIGN.md` — concise rationale for the main design choices.
- `docs/ROADMAP.md` — short phase and gate overview.
- `docs/tasks/phase-1.md` — commit-sized implementation checklist.
- `docs/workflow/branching-and-commits.md` — feature-branch and commit rules.
- `AGENTS.md` — concise safety rules and pointer to the docs map.
