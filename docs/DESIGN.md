# homecost design notes

The topic files linked from `SPEC.md` define required behavior. This file explains why the key choices fit the household's use.

## Dates and reporting

A payment date answers when money left; a cost month answers which month the owner wants the expense counted in. Utility bills can arrive or be paid after the month they belong to. Recording both lets reports answer both “what did this month cost?” and “when did the money leave?” `bill_date` is useful context but does not reliably assign a month. The first version assigns a whole bill to one month rather than splitting it across months.

Monthly, quarterly, and yearly totals by category answer the main spending questions. Month detail shows how a quarter or year accumulated. Current periods are marked “to date”; comparing unlike partial/full periods risks misleading results.

## Categories and details

Categories describe what an expense was for, not where it was bought. An online grocery purchase is still groceries; vendor/store records where it came from. Grocery-shopping trips use `groceries`; ready-to-eat meals and snacks bought separately use `meals & snacks`. Category values are lowercase and can be extended by the owner. A unit is useful for metered categories: amount divided by quantity gives cost per unit, while quantity trends help explain bill changes. One grocery expense per trip makes its count and average straightforward.

A monthly-bill flag means a payment is expected each month; it is not a general judgment that a category is “recurring.” Status is based on whether a payment is assigned to the month: current month with no entry is pending; a past month with no entry is missing. These labels describe the warehouse record, not whether a variable-date vendor considers a bill late. Metered comparisons use the previous calendar month only; if it has no usage entry, report comparison unavailable and say why rather than skipping back to an older month. CSV blanks for category and payment method use a visible `unassigned` value so the expense can be imported and corrected later; unknown nonblank values stop the import instead of being silently reclassified.

## Storage and operation

DuckDB keeps a small local warehouse in one file without a separate database server. Sequential CLI use fits one household and keeps operation simple. Keep the database local to its machine. The first version uses manual backups; automatic off-device copying can wait until it is needed.

Each installation represents one household. Time zone and currency are per-installation settings; starter categories are shared defaults, and added categories are per-installation data. This keeps the design reusable without adding multi-household or login features.
