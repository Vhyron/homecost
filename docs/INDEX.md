# Documentation map

Start here, then load only the files relevant to the current task. Do not read every linked document by default.

## Authority

- [SPEC index](SPEC.md) points to the approved, normative requirements. The topic files under `spec/` collectively are the behavior contract.
- [DECISIONS index](DECISIONS.md) points to settled owner choices. The topic files under `decisions/` hold the decision records. If these conflict with the SPEC, stop and ask.
- [DESIGN](DESIGN.md) explains rationale; it does not override the SPEC.
- [ROADMAP](ROADMAP.md) is the phase and gate overview. The detailed Phase 1 task list and branch policy are separate.
- [AGENTS.md](../AGENTS.md) contains safety rules for the coding agent. [README.md](../README.md) is the human-facing overview.

## Read for this task

| Task | Read |
|---|---|
| Change expense fields, dates, or validation | [Scope and data](spec/scope-and-data.md), plus [dates and reports decisions](decisions/dates-and-reports.md) when relevant. |
| Change guided entry, categories, vendors, payment methods, or CSV | [Entry and import](spec/entry-and-import.md), plus [lists and imports decisions](decisions/lists-and-imports.md). |
| Change a report | [Reports](spec/reports.md), plus [dates and reports decisions](decisions/dates-and-reports.md) and [DESIGN](DESIGN.md) as needed. |
| Change settings, backups, or restore | [Operations](spec/operations.md), plus [operations and engineering decisions](decisions/operations-and-engineering.md). |
| Plan or execute a Phase 1 task | [Phase 1 tasks](tasks/phase-1.md), [branch workflow](workflow/branching-and-commits.md), and only the SPEC/decision topics that task references. |
| Prepare the later Mac-to-Pi move | [ROADMAP](ROADMAP.md); the operational instructions belong in the future `runbook.md`. |

Requirement IDs stay attached to their canonical topic file and are used in tests, task entries, and commits.