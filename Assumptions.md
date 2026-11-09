# Assumptions & Logical Deductions - Axeom Operational Challenge

## 1. Data Integrity & Missing Values
- **Dropped Columns**: The `notice_onboard` column was removed because over 70-81% of its records were empty, indicating that onboarding instructions or face-blur requirements were largely untracked or inconsistently logged by the staff.
- **Operational Gaps**: Empty values in `production_board` (`client_approved`, `shoot_booking`) reflect administrative oversights, delayed internal log updates, or unlinked projects rather than total data corruption.

## 2. Lead-to-Booking Discrepancy (Question #3)
- **Lost Requests**: The significant gap between total inquiries (~113 leads) and confirmed bookings (~20 bookings) serves as quantitative evidence that client requests are getting lost due to slow response times, lack of follow-up tracking, or communication fragmentation across channels (Instagram, WhatsApp, Email).

## 3. Financial Reconciliation (Question #2)
- **Unpaid Balances**: Discrepancies or missing entries when matching `invoices.csv` with `payments.csv` highlight billing gaps, where services were delivered and invoiced but corresponding payments were never properly logged or collected.