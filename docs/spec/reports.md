# Reports

This is the normative home for R-01–R-06. Keep these requirement IDs stable for implementation tasks and tests.

| ID | Requirement |
|---|---|
| R-01 | Show spending totals by category for a month, quarter, or year, with month-by-month detail inside quarters and years. All amounts use the installation currency. Tests: `test_month_report_totals_by_category`, `test_quarter_report_totals_and_month_detail`, `test_year_report_totals_exclude_other_years`, `test_report_cli_shows_totals_with_month_detail`, `test_report_rejects_invalid_periods`. |
| R-02 | Provide both cost-month view (`cost_month`) and cash view (`paid_date`) for those periods. Test: `test_report_cli_supports_cost_month_and_paid_date_bases`. |
| R-03 | Label the current month, quarter, or year as “to date”. Do not compare an incomplete period with a completed previous period in v1. Test: `test_report_labels_current_period_to_date`. |
| R-04 | For groceries, show the number of expenses (trips) and average amount per trip. |
| R-05 | For metered categories, show monthly total, quantity, and cost per unit, plus usage and unit-cost changes from the previous calendar month. If that month has no usage entry, show “Comparison unavailable: no usage was recorded for [previous month].” Do not compare against an older month. |
| R-06 | For each monthly-bill category and month, use `cost_month`: report `recorded` if at least one expense is assigned to that month; `pending` if none is assigned in the current month; `missing` if none is assigned in a past month. Do not report future months. These labels describe records, not vendor lateness or unpaid invoices; `bill_date` does not determine status. Never present an unrecorded bill as a zero expense. |