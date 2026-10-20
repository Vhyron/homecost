# Dates, currency, and reports

These are settled owner decisions. The corresponding requirements are in [scope and data](../spec/scope-and-data.md) and [reports](../spec/reports.md).

| ID | Decision |
|---|---|
| DEC-04 | Keep `paid_date`, assigned `cost_month`, and optional `bill_date`. The owner assigns the cost month; payment and bill issue dates do not decide it. |
| DEC-10 | Reports cover month, quarter, and year, by category, with month detail and both cost-month and paid-date views. Current periods are “to date”; no same-point comparison in v1. |
| DEC-17 | Reject future `paid_date` values. Limit the gap between `paid_date` and `cost_month` to 12 calendar months in either direction. This leaves room for the observed 1–3 month utility-bill gaps while guarding against unusually distant assignments; old expenses with matching dates are not limited. |
| DEC-20 | Monthly bill status is based on `cost_month`: `recorded` if a payment is assigned to the month, `pending` if none is assigned in the current month, and `missing` if none is assigned in a past month. Do not report future months. These are record-status labels, not claims that a vendor is late or that an unpaid bill is being tracked; `bill_date` does not set status. |
| DEC-21 | Metered-category comparisons use the previous calendar month. If it has no usage entry, report comparison unavailable and explain why; never skip back to an older month. |
| DEC-26 | Use PHP and `Asia/Manila` as configurable per-installation default currency and time zone. |
| DEC-28 | Use one currency per installation. For this installation the default is PHP; manually convert any foreign-currency amount before entering it. Do not add per-expense currencies or exchange rates in v1. |