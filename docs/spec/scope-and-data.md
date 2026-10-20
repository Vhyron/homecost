# Scope and expense data

This is the normative home for scope, category defaults, and D-01–D-13. These requirements are part of the approved v1 SPEC; keep their IDs when changing this file.

## Purpose and scope

Homecost records household expenses and reports spending by category. Each installation serves one household. Time zone and currency are configurable; starter categories are seeded defaults that users can extend. Household data does not belong in the software or examples.

The first version runs on a Mac and should be portable to a dedicated Raspberry Pi later. Entry is through a CLI and CSV import. It includes manual backup and restore.

**Not in the first version:** API, web/mobile/desktop front end, receipt photos, splitting a bill across months, category groups, recurring-only reports, same-point comparisons of incomplete periods, scheduled backups, or automatic off-device copies.

## Starter categories and lists

Category values are lowercase, normalized when saved, and shown as a flat list. Initialization seeds these defaults on every installation; users can add categories during use but cannot replace the starter list before initialization.

| Category value | Unit | Monthly bill expected | Meaning |
|---|---|---:|---|
| `electricity` | kWh | Yes | Electricity utility bill. |
| `water` | m³ | Yes | Water utility bill. |
| `groceries` | — | No | One expense per grocery trip; no item-level tracking. |
| `meals & snacks` | — | No | Meals and snacks bought ready to eat, including dine-in, takeaway, delivery, and bakery food. If bought as part of a grocery trip, record them with `groceries`. |
| `drinking water` | gallons | No | A standard refill is 5 gallons; record total gallons bought. |
| `home appliances` | — | No | Durable household equipment, not its repair. |
| `wi-fi` | — | Yes | Household internet subscription. |
| `home supplies` | — | No | Household consumables and small items, such as sprays, alcohol, dustpans, and hangers. |
| `home maintenance & repairs` | — | No | Home or appliance repair work. |

A category can be added during use with a name, optional unit, and monthly-bill yes/no setting. Expense entry offers seeded and user-added categories. Duplicate normalized category values are refused. Punctuation remains significant. The system-reserved `unassigned` category is used for CSV rows without a category; it appears in reports and cannot be renamed or removed.

Vendors/stores are an optional managed list that starts empty. A vendor is a store/provider name, not an expense category; for example, groceries bought online remain `groceries`.

Payment methods are a separate managed list, initialized with `cash` and system-reserved `unassigned`. The owner can add methods such as GCash, Maya, BPI, or PNB; these are not a fixed enum or categories. Initialization never overwrites methods the owner has added. The `unassigned` method is used for CSV rows without a payment method and cannot be renamed or removed.

## Expense data and validation

| ID | Requirement |
|---|---|
| D-01 | Each expense has a required paid date, category, and positive amount. Vendor/store is optional. `cost_month` defaults to the paid month and can be set separately; it is the month the owner assigns the cost to. Optional `bill_date` records when a bill was issued and never determines `cost_month`. Do not split bills across months. Tests: `test_add_expense_defaults_cost_month_to_paid_month`, `test_add_expense_accepts_cost_month_and_bill_date_independently`, `test_add_expense_rejects_missing_required_fields`. |
| D-02 | A September utility bill paid in October can be assigned to September. A later payment date does not move its cost into the payment month. |
| D-03 | Money uses `Decimal` in Python and `DECIMAL` in DuckDB; never use floats for amounts. Amounts have at most two decimal places. Tests: `test_expense_preserves_decimal_amount`, `test_expense_rejects_more_than_two_decimal_places`. |
| D-04 | Category values are trimmed, repeated spaces collapsed, and converted to lowercase when saved. Names that normalize to the same value are duplicates. Punctuation is significant. Tests: `test_add_category_normalizes_name`, `test_add_category_rejects_normalized_duplicate`. |
| D-05 | Categories with a unit require a positive quantity; categories without a unit reject quantity. Quantity uses up to three decimal places. Drinking-water quantity is total gallons (5 per standard container). Tests: `test_metered_expense_requires_positive_quantity`, `test_metered_expense_stores_quantity_to_three_places`, `test_quantity_rejects_precision_over_three_places`, `test_non_metered_expense_rejects_quantity`. |
| D-06 | A category marked monthly-bill-expected is eligible for a bill-status report. |
| D-07 | “Today” uses the configured household time zone. Reject a `paid_date` later than today. The calendar-month gap between `paid_date` and `cost_month` may be at most 12 months in either direction; this does not limit how far back an expense may be recorded. Timestamps, if stored, are UTC. Tests: `test_today_uses_configured_household_timezone`, `test_rejects_paid_date_after_household_today`, `test_rejects_cost_month_gap_over_twelve_calendar_months`, `test_accepts_twelve_month_gap_and_old_matching_dates`. |
| D-08 | An entry that fails validation leaves no partial data behind. |
| D-09 | Database schema changes use ordered migrations; initialization is repeatable and does not overwrite existing category, vendor, or payment-method data. Test: `test_initialize_is_repeatable_and_adds_seeds_without_overwriting`. |
| D-10 | Every expense has a required payment method selected from the managed list. Tests: `test_expense_requires_managed_payment_method`, `test_expense_accepts_managed_payment_method`. |
| D-11 | Vendor names are trimmed, repeated spaces collapsed, and converted to lowercase when saved, like categories. Values that normalize to the same name are duplicates; punctuation is significant. Tests: `test_add_vendor_normalizes_name`, `test_add_vendor_rejects_normalized_duplicate`. |
| D-12 | Payment-method names use the same normalization and duplicate rules as categories and vendors. Tests: `test_add_payment_method_normalizes_name`, `test_add_payment_method_rejects_normalized_duplicate`. |
| D-13 | Each installation uses one currency for all expenses. The default is PHP. Convert any foreign-currency expense manually before entry; do not store per-expense currencies or exchange rates. Test: `test_installation_currency_defaults_to_php_and_is_not_per_expense`. |