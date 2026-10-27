# RationSathi — Smart and Transparent PDS Management System

A software-only educational prototype for managing beneficiary records, ration stock, distribution transactions, and complaints. Built with Python Flask and SQLite so it can run locally without paid services or hardware.

> **Prototype disclaimer:** This is a demonstration application using fictional sample data. It is not connected to India's official PDS systems and must not be used to make real eligibility decisions or store real beneficiary data.

## Features
- Role-based demo accounts: administrator, shop operator, beneficiary
- Dashboard with beneficiary, stock, transaction, and complaint summaries
- Beneficiary list
- Stock update and inventory view
- Distribution recording with stock validation
- Transaction history and basic reports
- Complaint submission and status tracking
- Password hashing and parameterized SQL queries
- SQLite database automatically initialized on first run

## Technology
- Python 3.10+
- Flask
- SQLite
- HTML/CSS/Jinja templates

## Setup
1. Install Python 3.10 or later.
2. Open a terminal in this folder.
3. Create and activate a virtual environment:

   **Windows**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Set a secret key before running outside a local demo:
   - Windows PowerShell: `$env:SECRET_KEY="replace-with-a-long-random-secret"`
   - macOS/Linux: `export SECRET_KEY="replace-with-a-long-random-secret"`
6. Run:
   ```bash
   python app.py
   ```
7. Open http://127.0.0.1:5000 in your browser.

The database file `ration_sathi.db` is created automatically on first run.

## Demo accounts
| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `Admin@123` |
| Shop operator | `operator` | `Operator@123` |
| Beneficiary | `beneficiary` | `User@123` |

Change/remove demo credentials before any deployment. The beneficiary account is linked to sample card `TN-1001`.

## Project structure
```text
RationSathi/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── docs/
│   ├── ARCHITECTURE.md
│   └── TEST_CASES.md
├── sample_data/
│   └── sample_data.json
├── tests/
│   └── test_app.py
└── templates/
    ├── base.html
    ├── login.html
    ├── dashboard.html
    ├── beneficiary_dashboard.html
    ├── beneficiaries.html
    ├── stock.html
    ├── distribute.html
    ├── transactions.html
    ├── complaints.html
    └── reports.html
```

## Tests
Install dependencies and run:
```bash
python -m unittest discover -s tests -v
```

## Limitations and future work
- Current prototype uses SQLite and fictional data.
- Beneficiary view is a demonstration account, not a live identity integration.
- No official government API, SMS gateway, or biometric service is connected.
- Local-language voice assistance, offline sync across devices, and production-grade audit logs are future enhancements.
- For real deployment, add CSRF protection, rate limiting, secure secret management, access reviews, backups, HTTPS, privacy safeguards, and authorized data integration.

## License
MIT. See `LICENSE`.
