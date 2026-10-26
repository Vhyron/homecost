# Runbook

Task-based instructions for operating homecost. Requirements live in the [SPEC](SPEC.md); this file describes how to use them day to day. All commands run with `uv run homecost …` from the project directory.

## Start using it (first time or fresh start)

1. Confirm `~/.homecost` does not exist (or back it up elsewhere first if it does).
2. `uv run homecost init` — creates the database and seeds the starter categories and payment methods. Initialization is add-only; it never overwrites existing list data.
3. `uv run homecost settings` — check the time zone and currency before entering the first expense. Currency is locked once the first expense exists.

**Never initialize into a directory that holds real data you want to keep.**

## Daily use

| Task | Command |
|---|---|
| Record one expense | `uv run homecost add` — guided prompts in order: paid date, amount, category, payment method, vendor, cost month, bill date, quantity (metered categories only). Enter accepts the defaults and skips optional fields; Ctrl+C cancels without writing anything. |
| Import a CSV batch | `uv run homecost import FILE.csv` — the whole file is validated first; nothing is imported if any row is invalid. Review duplicate warnings row by row. |
| Review expenses | `uv run homecost list`, optionally `--category CATEGORY` or `--payment-method METHOD`. Use `unassigned` for either filter to find records missing a classification. |
| Fix a mistake | `uv run homecost edit ID` (ID from `list`). |
| Remove a record | `uv run homecost delete ID` — asks for confirmation; deletion is permanent. Restore from a backup if you deleted the wrong thing. |

## Managing categories, vendors, and payment methods

Each list supports `list`, `add`, `rename OLD NEW`, and `remove NAME` under `homecost categories`, `homecost vendors`, and `homecost payment-methods`.

- Renaming updates every existing expense and future entries; you are shown how many records are affected.
- Removing archives a value: historical expenses and reports keep it, but it is no longer offered for new entries. Adding the same name again reactivates it.
- `unassigned` is reserved and cannot be renamed or removed. An individual expense can be corrected with `edit`.
- List commands show both active and archived values.

## Reports

```bash
uv run homecost report 2025-09 --basis cost_month   # a month
uv run homecost report 2025-Q3 --basis paid_date    # a quarter
uv run homecost report 2025 --basis cost_month      # a year
```

- `cost_month` answers "what month was this cost for"; `paid_date` answers "when did the money leave". For a September electricity bill paid in October: cost-month September, paid-date October.
- Each report shows per-category totals, period detail, a grand total, grocery trip counts and averages, metered usage with unit costs and previous-month comparison, and monthly-bill status (`recorded`/`pending`/`missing`).
- Current periods are labeled "to date". A `missing` month means no expense is recorded for it — check the actual bill before assuming the amount was zero.

## Backups

```bash
uv run homecost backup
```

- Backups are written to `~/.homecost/backups/homecost-YYYYMMDD-HHMMSS.duckdb` and are verified on creation.
- The 5 newest backups are kept by default (change with `homecost settings set backup-retention N`, 1–365). Old backups are pruned only after a new backup verifies; a failed backup deletes nothing.
- **A backup is only as good as its last restore test.** After important changes, or at least occasionally, restore the newest backup to a scratch path and check it (see below).

### Verify a backup

```bash
uv run homecost restore ~/.homecost/backups/<file> --to /tmp/verify.duckdb
uv run python -c "import duckdb; con = duckdb.connect('/tmp/verify.duckdb'); print(con.sql('select count(*), sum(amount) from expenses')); con.close()"
rm /tmp/verify.duckdb
```

The counts and total should match `homecost list`. (Run the query from the project directory so `uv` provides the `duckdb` module.)

## Recovery

If the live database is lost, corrupted, or suspect:

1. Stop. Do not run `init` — it would create a fresh, empty database at the same path.
2. Pick the newest trusted backup from `~/.homecost/backups/`.
3. `uv run homecost restore ~/.homecost/backups/<file> --to ~/.homecost/homecost.duckdb` — this works only if the live file is already gone or moved aside; restore never overwrites.
4. Verify with `homecost list` and a spot-check report, then create a fresh backup.

## Known limitations

- Backup is a file copy taken after a DuckDB checkpoint; it is safe only because one homecost process at a time touches the database. Never run homecost from two places at once, and never store the database on a network share.
- Valid currency codes come from a static ISO 4217 list in the code. If a code you need is rejected, ask to have it added.
- The database and backups contain private household data. Keep them off network shares and out of any repository or cloud service.

## Raspberry Pi migration (not yet written)

Instructions for moving the household system from the Mac to a Pi will be added to this file in Phase 3, once the actual hardware is known. Until then the Mac is the live system.
