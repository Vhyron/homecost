# Roadmap

Follow [the docs map](INDEX.md); load only the phase and task files relevant to the current work.

## Phase 0: Specification development

- [x] Approve the SPEC, README, and roadmap.
- [x] Complete the cross-document consistency pass and settle the CLI command surface.
- [x] Prepare the commit-sized Phase 1 task list and branch workflow.

**Gate 0:** Approved. The documentation baseline is ready for its initial Git commit. Phase 1 begins after that commit and branch setup.

## Phase 1: Build and verify on the Mac

Follow the [Phase 1 task checklist](tasks/phase-1.md) and [branch workflow](workflow/branching-and-commits.md). Build from the approved SPEC; do not add first-version-excluded API, front end, receipt, or server-only behavior.

**Before using real household data:** run the full test suite and synthetic-data demo on Mac, reconcile report totals against source bills or statements, and create a backup that restores successfully to a separate file.

**Gate 1:** All SPEC requirements pass; the demo works; totals reconcile; backup and restore are verified; the owner approves real-data use.

## Phase 2: Use and refine

- Use the CLI and CSV import for household expenses.
- Keep a short friction list of mistakes, missing reports, and confusing steps.
- Change the SPEC only when the owner agrees; test each agreed change before building it.

**Gate 2:** The owner has used the warehouse and decided whether the starter categories and reports are adequate.

## Phase 3: Move to a Raspberry Pi (later)

When hardware is available, back up the Mac database, restore it on the Pi, and verify reports before switching live entry. Keep the database and application together, not on a network share. Write concise task-based CLI/CSV usage, backup, restore, recovery, and Mac-to-Pi migration steps in `docs/runbook.md` once the actual hardware is known, before relying on the Pi as the live system.

**Gate 3:** The Pi restore and reports are verified, the Mac copy is retired from live entry, and the runbook covers routine operation and recovery.