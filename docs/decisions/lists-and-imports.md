# Categories, managed lists, and imports

These are settled owner decisions. Normative behavior is in [scope and data](../spec/scope-and-data.md) and [entry and import](../spec/entry-and-import.md).

| ID | Decision |
|---|---|
| DEC-07 | Category values are normalized to lowercase. Users can add categories; show a flat list, with groups deferred until needed. |
| DEC-08 | Vendor/store is optional, uses a managed list, and starts with no seeded vendors. |
| DEC-16 | Payment method is required on every expense and comes from a managed list, separate from categories and vendors. Initialize it with `cash` and reserved `unassigned`; the owner can add methods such as GCash, Maya, BPI, and PNB. It is not a fixed enum. |
| DEC-18 | In CSV imports, a missing or blank category or payment method maps to reserved `unassigned`; a blank optional vendor stays empty. A nonblank unknown category, vendor, or payment method rejects the whole import with an actionable row-level error. Do not silently remap or auto-create unknown values. |
| DEC-19 | Keep `unassigned` as a reserved system category so missing CSV classifications remain visible in reports and can be corrected later. |
| DEC-22 | Use an exact-match duplicate check for manual entry and CSV import. For manual entry, warn and let the owner confirm. For each matching CSV row, let the owner skip it or import it anyway; import accepted rows together and report the results. |
| DEC-23 | Category creation requires an explicit yes/no answer for whether a monthly bill is expected; do not default it. |
| DEC-24 | Normalize vendor names like category values: trim, collapse repeated spaces, lowercase, and treat normalized duplicates as the same vendor; punctuation is significant. |
| DEC-25 | Normalize payment-method names the same way as category and vendor values, for consistency. |
| DEC-37 | Renaming a category, vendor, or payment method updates the label on all existing expenses and future entries; confirm and report the number of affected expenses. |
| DEC-38 | Removing a category, vendor, or payment method requires confirmation and archives it, preserving historical expenses and reports while excluding it from new entries/imports. Adding an archived name reactivates it. |
| DEC-39 | Keep `unassigned` as a reserved system value. Correct an individual expense through `homecost edit`; use category or payment-method filters to find unassigned records. |