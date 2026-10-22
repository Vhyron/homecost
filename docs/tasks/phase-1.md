# Phase 1: Commit-sized tasks

Work through this checklist in order. Each row is one commit; its SPEC ID is the acceptance contract. Read the relevant file from the [SPEC index](../SPEC.md), not every spec topic. Follow the [branching and commit workflow](../workflow/branching-and-commits.md).

For each SPEC task: write the failing test first, implement only that requirement, run the targeted test and full suite on the feature branch, record the passing test name beside the requirement in the SPEC, then merge to `dev`. Record the commit's short hash in the table after merging. The bootstrap task has no SPEC ID.

| Done | ID | Commit-sized task | Commit hash |
|---|---|---|---|
| [x] | Bootstrap | Create the Python package, CLI entry point, dependency lock, and pytest setup; no expense behavior yet. | e89978a |
| [x] | D-01 | Store required expense fields, cost-month default/override, and optional bill date. | 5314893 |
| [x] | D-03 | Preserve monetary precision with `Decimal` and DuckDB `DECIMAL`. | 10843d7 |
| [x] | D-09 | Add ordered migrations and repeatable initialization with add-only seeds. | 58626e1 |
| [x] | D-04 | Normalize category names and reject normalized duplicates. | 4c229a8 |
| [x] | D-11 | Normalize vendor names and reject normalized duplicates. | c76602b |
| [x] | D-12 | Normalize payment-method names and reject normalized duplicates. | 61305d8 |
| [x] | D-10 | Require each expense to use a managed payment method. | 4157af9 |
| [x] | D-05 | Validate metered-category quantity and precision rules. | c233293 |
| [x] | D-13 | Enforce one installation currency and manual conversion semantics. | a6469c1 |
| [x] | I-10 | Add validated settings display/update, persistence, defaults, and safeguards. | 0ada83b |
| [x] | D-07 | Enforce household-time-zone “today”, future-date refusal, and the 12-month assignment gap. | 1f83cdc |
| [x] | D-02 | Test that late-paid utility expenses can remain assigned to the earlier cost month. | ad1283a |
| [x] | D-06 | Store monthly-bill eligibility on categories. | a52c09d |
| [x] | D-08 | Make invalid expense writes atomic. | eef78b3 |
| [x] | I-02 | Implement guided single-expense entry. | e2a1533 |
| [x] | I-03 | Add guided category creation with explicit monthly-bill choice. | 55834b8 |
| [x] | I-08 | Add managed payment-method creation. | f35a7d5 |
| [x] | I-04 | Validate CSV rows before any write and report all row errors. | ed70db9 |
| [x] | I-05 | Parse the specified CSV columns, defaults, and managed-list values. | 96c4817 |
| [x] | I-01 | Verify CLI and CSV writes use the shared service validation. | fe3fd20 |
| [x] | I-06 | Edit an expense atomically with creation validation. | 7f5571c |
| [x] | I-07 | Confirm and permanently delete one expense. | 341a59f |
| [x] | I-09 | Add shared exact-match duplicate detection and per-row CSV review. | 1c7bbae |
| [x] | I-11 | Rename categories, vendors, or payment methods across existing expenses and future entry. | 911b1c1 |
| [x] | I-12 | Archive removed managed values without changing historical expenses. | fbda975 |
| [x] | I-14 | Show active/archived managed values and reactivate an archived value on add. | 3ac3854 |
| [x] | I-13 | Filter unassigned expenses and correct them individually. | 1eeb155 |
| [x] | R-01 | Report monthly, quarterly, and yearly category totals with period detail. | b7fd0c0 |
| [x] | R-02 | Support cost-month and paid-date report bases. | 3b949ef |
| [x] | R-03 | Mark current periods “to date” and avoid incomplete-period comparisons. | ef9cf47 |
| [x] | R-04 | Report grocery trip counts and averages. | c4406ba |
| [x] | R-05 | Report metered usage/unit costs and previous-month comparison behavior. | 0e45518 |
| [x] | R-06 | Report monthly-bill record statuses. | 0cb7105 |
| [x] | O-02 | Create, verify, name, retain, and safely rotate local backups. | 54e729c |
| [x] | O-03 | Restore to a new path without overwriting an existing database. | 13fe9d3 |
| [x] | I-02 | Fix guided entry per the updated I-02: reject invalid numbered choices, offer add-new-category, use the specified prompt order and wording, and parse cost month as YYYY-MM. | 266dd2d |
| [x] | — | Present `list` output as an aligned table and show an empty vendor as blank. | d9b3855 |
| [ ] | I-02 | Reorder guided entry prompts so amount follows paid date and precedes category, per the corrected I-02. | |

Before using real household data, run the full documented test suite and synthetic-data demo on Mac, reconcile report totals against source bills or statements, and create a backup that restores successfully to a separate file.