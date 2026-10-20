# Branching and commits

- Put the approved documentation baseline on `main`, then create `dev` from it.
- For each SPEC task, create a short-lived `feat/<SPEC-ID>-slug` branch from the latest `dev`. For bootstrap, use `chore/bootstrap`.
- Write the failing test first, implement only that requirement, then run the targeted test and full suite on the feature branch before merging it into `dev`.
- Each checklist item is one commit. Use a conventional commit subject with its SPEC ID, such as `feat(csv): validate CSV headers [I-05]` or `fix(dates): reject future paid dates [D-07]`.
- After merging into `dev`, check the task off and record the short commit hash in its `Commit hash` cell in the task table.
- Once all tasks are integrated, verify the full suite and demo on `dev`; merge `dev` into `main` only at the release gate. Do not commit feature work directly to `main`.

Local branches do not enforce protection. Follow this workflow manually; configure remote branch protection if a hosted remote is added.