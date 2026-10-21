# Settings, backup, and restore

This is the normative home for settings and O-02–O-03. Requirement IDs remain stable for tasks and tests.

## Commands

| Command | Purpose |
|---|---|
| `homecost settings` / `homecost settings set KEY VALUE` | Show or change supported per-installation settings. |
| `homecost report PERIOD --basis BASIS` | Report for a month (`YYYY-MM`), quarter (`YYYY-Qn`), or year (`YYYY`); `BASIS` is `cost_month` or `paid_date`. |
| `homecost backup` | Create a verified local backup. |
| `homecost restore BACKUP --to DATABASE` | Restore a backup to a new database path. |

## Settings and technical constraints

| ID | Requirement |
|---|---|
| I-10 | `homecost settings` shows current settings and data/backup paths; `homecost settings set KEY VALUE` changes only `timezone`, `currency`, or `backup-retention`. Settings are stored in the database and included in backups. Reject unknown keys and invalid values without changing stored settings. Time zone must be a valid IANA time-zone name; currency must be a valid three-letter ISO 4217 code. Currency can be changed only before the first expense. A time-zone change requires confirmation and does not rewrite stored dates. Backup retention must be an integer from 1 to 365; a reduced limit is applied after the next successfully verified backup. Tests: `test_settings_have_defaults`, `test_invalid_setting_is_rejected_without_change`, `test_currency_and_retention_settings_persist`, `test_timezone_change_requires_confirmation`, `test_currency_cannot_change_after_first_expense`, `test_settings_cli_shows_defaults_and_paths`, `test_settings_cli_confirms_timezone_change`. |

- One household and one user per installation; no login system.
- The default database path is `~/.homecost/homecost.duckdb`; settings are stored in the database and included in backups. `homecost settings` shows current settings and data/backup paths.
- Supported setting keys are `timezone`, `currency`, and `backup-retention`. Currency and time zone default to PHP and `Asia/Manila`; backup retention defaults to 5. All expense amounts use the installation currency; foreign-currency amounts are converted manually before entry.
- Reject unknown keys and invalid values without changing stored settings. Time zone must be a valid IANA time-zone name; currency must be a valid three-letter ISO 4217 code. Currency can be changed only before the first expense. A time-zone change requires confirmation and does not rewrite stored dates. Backup retention must be an integer from 1 to 365; a reduced limit is applied after the next successfully verified backup.
- Use DuckDB as a local file, one homecost command at a time. Do not store it on a network share.
- Use Python 3.11 or newer, `argparse` for the CLI, and `pytest` for tests. Use `uv` for environment and dependency management; pin runtime dependencies in `pyproject.toml`, commit `uv.lock`, and preserve practical portability to a Raspberry Pi.
- The database and backups contain private household data. Do not commit them or send them to an outside service.

## Backup and restore requirements

| ID | Requirement |
|---|---|
| O-02 | `homecost backup` creates a consistent, restore-checked backup under `~/.homecost/backups/`, named `homecost-YYYYMMDD-HHMMSS.duckdb` using household local time. Add a suffix if needed to avoid overwriting a same-second backup. Retain the newest 5 local backups by default. Delete older backups beyond the configured limit only after a new backup is successfully verified; if backup creation or verification fails, delete nothing. Tests: `test_backup_creates_verified_timestamped_copy`, `test_backup_suffix_prevents_same_second_collision`, `test_failed_verification_deletes_nothing`, `test_backup_rotation_keeps_newest_configured_count`, `test_backup_cli_uses_backup_retention_setting`. |
| O-03 | `homecost restore BACKUP --to DATABASE` restores to a new path and refuses to overwrite an existing database. |