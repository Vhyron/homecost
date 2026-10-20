# homecost agent instructions

Start with [the docs map](docs/INDEX.md). Read only the SPEC and decision topics relevant to the current task; do not load every docs file by default. If a requirement is unclear or conflicts with a settled decision, stop and ask.

## Non-negotiable safety rules

- One homecost process at a time against a DuckDB file. Tests use temporary directories.
- Never touch real household data. Use temporary data or synthetic demo data; never run `init`, `import`, `delete`, or `restore` against the owner's real database.
- All writes go through `service.py`; keep validation there, not only in the CLI or importer.
- Schema changes use new ordered migrations. Never edit a released migration. Reports belong in SQL views.
- Use `Decimal` in Python and `DECIMAL` in DuckDB. Never use floats for amounts.
- “Today” comes from the configured household time zone, never the machine-local date.
- Use `uv`, exact dependency pins, and commit `uv.lock`. Do not add dependencies without owner approval.
- Initialization only adds seeds; it must not overwrite existing managed-list data.
- Do not send household data to outside services or build features excluded from the SPEC without owner approval.

## Change workflow

- Follow the one-task/one-commit plan in [Phase 1 tasks](docs/tasks/phase-1.md) and the [branch workflow](docs/workflow/branching-and-commits.md).
- For a SPEC requirement, write its failing test first, implement only that requirement, run the targeted test and full suite, then record the passing test name beside the requirement in its canonical SPEC topic file.
- When changing a CLI command or setting, update its canonical SPEC topic and README reference.
- Use human-readable errors that say what is wrong and what to do.
- If a needed decision is missing, add an `OPEN-nn` row to the relevant decision topic and stop.

## Done means

Behavior matches the SPEC; tests pass; relevant SPEC evidence and README text are current; synthetic demo works; tell the owner what changed and any unresolved risk.