# Product scope and starter defaults

These are settled owner decisions. Their normative behavior is in the linked SPEC topics.

| ID | Decision |
|---|---|
| DEC-01 | Build the household cost warehouse first. First-version entry is CLI and CSV; no API or front end. |
| DEC-02 | One household and one user per installation. |
| DEC-05 | Start on a Mac; keep the first version portable to a dedicated Raspberry Pi later. Pi deployment is deferred. |
| DEC-09 | One grocery trip is one expense; do not track grocery line items in v1. |
| DEC-13 | Each installation can configure its time zone and currency. Starter categories are defaults seeded at initialization; categories can be added during use. Do not bake owner-specific dates or household data into the software. |
| DEC-14 | Use the shared starter categories defined in [scope and data](../spec/scope-and-data.md). Utilities and Wi-Fi are monthly bills; units and meanings are defined there. |
| DEC-15 | “Online” describes where an item was bought, not what it is. Do not create an online-purchases category in v1. |
| DEC-35 | Seed the same starter categories during initialization for every installation. Allow users to add categories afterward; do not add a pre-initialization category replacement workflow in v1. |
| DEC-36 | `meals & snacks` is a starter category for ready-to-eat meals and snacks, including dine-in, takeaway, delivery, and bakery food. Food bought as part of a grocery trip stays in `groceries`. |