# Storage, backups, and engineering workflow

These are settled owner decisions. Normative requirements are in [operations](../spec/operations.md); branch/task workflow is in [branching and commits](../workflow/branching-and-commits.md).

| ID | Decision |
|---|---|
| DEC-03 | Use DuckDB as a local database file; use one homecost command at a time. |
| DEC-06 | Store money as `DECIMAL` in DuckDB and `Decimal` in Python; no floating-point amounts. |
| DEC-11 | Manual backup and restore are in v1; automatic off-device copying is deferred. |
| DEC-12 | Expenses can be edited and deleted. Edits use creation validation; deletes are permanent and confirmed. No audit log in v1. |
| DEC-27 | Keep 5 local backups by default. Delete backups beyond the configured limit only after a new backup is successfully verified; failed backup creation or verification never deletes old backups. A reduced limit takes effect after the next successful backup. |
| DEC-29 | Use `uv` to manage the Python environment and dependencies; commit `uv.lock` for reproducible installs. |
| DEC-30 | Use Python 3.11+, the standard-library `argparse` for the CLI, and `pytest` for automated tests. |
| DEC-31 | Change per-installation settings through a `homecost settings` command, not a config file or shell environment variables. |
| DEC-32 | Use guided CLI entry for one expense at a time, with numbered category and payment-method choices. Pressing Enter skips the optional vendor. Use CSV import for batches. |
| DEC-33 | Reject unsupported settings and invalid values without changing the stored value. Time zone must be a valid IANA name and currency a valid three-letter ISO 4217 code. Currency cannot change after the first expense; time-zone changes require confirmation and do not rewrite stored dates. Backup retention is limited to 1–365 whole backups. |
| DEC-34 | Store the database at `~/.homecost/homecost.duckdb` by default and local backups in `~/.homecost/backups/`. Name backups with a household-local timestamp and prevent filename collisions. |