# Technical Design Document

## 1. Purpose
RationSathi is a software-only prototype for demonstrating more transparent ration-shop record management. It is not an official PDS service.

## 2. Architecture
```text
Browser (beneficiary/operator/admin)
              |
              v
Flask web application
  |       |        |
  |       |        +-- Role checks and session login
  |       +----------- Inventory, distribution, complaints, reports
  +------------------- Input validation and business rules
              |
              v
         SQLite database
```

## 3. Main modules
- Authentication: verifies hashed passwords and stores role in the session.
- Dashboard: summarizes counts and recent activity.
- Beneficiaries: lists sample beneficiary records for staff roles.
- Stock: adds/updates commodity stock.
- Distribution: validates beneficiary, commodity, positive quantity, and available stock before recording a transaction.
- Transactions: displays distribution history.
- Complaints: creates complaints and allows staff to update status.
- Reports: totals recorded distribution by commodity.

## 4. Data model
- `users(id, username, password_hash, role, full_name)`
- `beneficiaries(id, card_number, name, village, household_size, monthly_entitlement_kg)`
- `stock(id, commodity, quantity_kg)`
- `transactions(id, card_number, commodity, quantity_kg, created_at, recorded_by)`
- `complaints(id, card_number, category, description, status, created_at)`

## 5. Security considerations
- Passwords are stored as Werkzeug password hashes.
- SQL statements use parameterized queries.
- Routes check user roles.
- The development secret key must be replaced for deployment.
- This teaching prototype does not yet include CSRF protection, account lockout, password reset, or a complete audit trail. Do not deploy with real personal data until these controls are implemented.

## 6. Important assumptions
- All included records are fictional sample data.
- Beneficiary self-service is mapped to sample card `TN-1001`.
- Stock and transactions are entered by authorized demo staff.
- The software cannot physically verify the actual weight or independently confirm an in-person handover.
