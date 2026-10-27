# Test Cases

Run automated checks using `python -m unittest discover -s tests -v`.

| ID | Scenario | Expected result |
|---|---|---|
| TC01 | Open application root without login | Redirect to login |
| TC02 | Login with valid operator credentials | Dashboard loads |
| TC03 | Login with incorrect password | Error message shown |
| TC04 | Beneficiary opens staff-only stock page | Redirect to dashboard with permission message |
| TC05 | Staff updates existing stock | Stock quantity changes |
| TC06 | Staff records valid distribution | Transaction is added and stock decreases |
| TC07 | Distribution exceeds available stock | Transaction rejected; stock unchanged |
| TC08 | Beneficiary submits complaint | Complaint appears in beneficiary list |
| TC09 | Staff changes complaint status | Status is updated |
| TC10 | Staff opens reports | Total distribution and commodity summary appear |
