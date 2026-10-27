import os
import sqlite3
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.environ.get("RATION_SATHI_DB", os.path.join(APP_DIR, "ration_sathi.db"))
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-development-secret")

app = Flask(__name__)
app.secret_key = SECRET_KEY

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('beneficiary','operator','admin')),
        full_name TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS beneficiaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_number TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        village TEXT NOT NULL,
        household_size INTEGER NOT NULL DEFAULT 1,
        monthly_entitlement_kg REAL NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        commodity TEXT UNIQUE NOT NULL,
        quantity_kg REAL NOT NULL DEFAULT 0 CHECK(quantity_kg >= 0)
    );
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_number TEXT NOT NULL,
        commodity TEXT NOT NULL,
        quantity_kg REAL NOT NULL CHECK(quantity_kg > 0),
        created_at TEXT NOT NULL,
        recorded_by TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_number TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Open',
        created_at TEXT NOT NULL
    );
    """)
    users = [
        ("admin", generate_password_hash("Admin@123"), "admin", "System Administrator"),
        ("operator", generate_password_hash("Operator@123"), "operator", "Ration Shop Operator"),
        ("beneficiary", generate_password_hash("User@123"), "beneficiary", "Demo Beneficiary"),
    ]
    for row in users:
        db.execute("INSERT OR IGNORE INTO users(username,password_hash,role,full_name) VALUES(?,?,?,?)", row)
    beneficiaries = [
        ("TN-1001", "Lakshmi", "Demo Village", 4, 20.0),
        ("TN-1002", "Ravi", "North Street", 3, 15.0),
        ("TN-1003", "Meena", "Lake Road", 5, 25.0),
    ]
    for row in beneficiaries:
        db.execute("""INSERT OR IGNORE INTO beneficiaries
            (card_number,name,village,household_size,monthly_entitlement_kg)
            VALUES(?,?,?,?,?)""", row)
    for row in [("Rice", 500.0), ("Wheat", 200.0), ("Sugar", 80.0)]:
        db.execute("INSERT OR IGNORE INTO stock(commodity,quantity_kg) VALUES(?,?)", row)
    db.commit()
    db.close()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                flash("You do not have permission to access that page.", "error")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["full_name"] = user["full_name"]
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    stats = {
        "beneficiaries": db.execute("SELECT COUNT(*) FROM beneficiaries").fetchone()[0],
        "commodities": db.execute("SELECT COUNT(*) FROM stock").fetchone()[0],
        "transactions": db.execute("SELECT COUNT(*) FROM transactions").fetchone()[0],
        "open_complaints": db.execute("SELECT COUNT(*) FROM complaints WHERE status='Open'").fetchone()[0],
    }
    recent = db.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT 5").fetchall()
    stock = db.execute("SELECT * FROM stock ORDER BY commodity").fetchall()
    if session["role"] == "beneficiary":
        card = db.execute("SELECT * FROM beneficiaries WHERE card_number='TN-1001'").fetchone()
        recent = db.execute("SELECT * FROM transactions WHERE card_number='TN-1001' ORDER BY id DESC LIMIT 5").fetchall()
        return render_template("beneficiary_dashboard.html", stats=stats, card=card, recent=recent)
    return render_template("dashboard.html", stats=stats, recent=recent, stock=stock)

@app.route("/beneficiaries")
@login_required
@roles_required("admin", "operator")
def beneficiaries():
    rows = get_db().execute("SELECT * FROM beneficiaries ORDER BY name").fetchall()
    return render_template("beneficiaries.html", rows=rows)

@app.route("/stock", methods=["GET", "POST"])
@login_required
@roles_required("admin", "operator")
def stock_page():
    db = get_db()
    if request.method == "POST":
        commodity = request.form.get("commodity", "").strip()
        try:
            quantity = float(request.form.get("quantity", ""))
            if not commodity or quantity < 0:
                raise ValueError()
            existing = db.execute("SELECT id FROM stock WHERE commodity=?", (commodity,)).fetchone()
            if existing:
                db.execute("UPDATE stock SET quantity_kg=? WHERE commodity=?", (quantity, commodity))
            else:
                db.execute("INSERT INTO stock(commodity,quantity_kg) VALUES(?,?)", (commodity, quantity))
            db.commit()
            flash("Stock updated successfully.", "success")
        except (ValueError, TypeError):
            flash("Enter a valid commodity and non-negative quantity.", "error")
        return redirect(url_for("stock_page"))
    rows = db.execute("SELECT * FROM stock ORDER BY commodity").fetchall()
    return render_template("stock.html", rows=rows)

@app.route("/distribute", methods=["GET", "POST"])
@login_required
@roles_required("admin", "operator")
def distribute():
    db = get_db()
    beneficiary_rows = db.execute("SELECT * FROM beneficiaries ORDER BY name").fetchall()
    stock_rows = db.execute("SELECT * FROM stock ORDER BY commodity").fetchall()
    if request.method == "POST":
        card = request.form.get("card_number", "").strip()
        commodity = request.form.get("commodity", "").strip()
        try:
            qty = float(request.form.get("quantity_kg", ""))
            beneficiary = db.execute("SELECT * FROM beneficiaries WHERE card_number=?", (card,)).fetchone()
            item = db.execute("SELECT * FROM stock WHERE commodity=?", (commodity,)).fetchone()
            if not beneficiary or not item or qty <= 0:
                raise ValueError()
            if qty > item["quantity_kg"]:
                flash("Insufficient stock. Transaction was not recorded.", "error")
            else:
                db.execute("UPDATE stock SET quantity_kg=quantity_kg-? WHERE commodity=?", (qty, commodity))
                db.execute("""INSERT INTO transactions(card_number,commodity,quantity_kg,created_at,recorded_by)
                    VALUES(?,?,?,?,?)""",
                    (card, commodity, qty, datetime.now().strftime("%Y-%m-%d %H:%M"), session["username"]))
                db.commit()
                flash("Distribution recorded and stock updated.", "success")
                return redirect(url_for("transactions"))
        except (ValueError, TypeError):
            flash("Select a valid beneficiary, commodity, and positive quantity.", "error")
    return render_template("distribute.html", beneficiaries=beneficiary_rows, stock=stock_rows)

@app.route("/transactions")
@login_required
def transactions():
    db = get_db()
    if session["role"] == "beneficiary":
        rows = db.execute("""SELECT * FROM transactions WHERE card_number='TN-1001'
            ORDER BY id DESC""").fetchall()
    else:
        rows = db.execute("SELECT * FROM transactions ORDER BY id DESC").fetchall()
    return render_template("transactions.html", rows=rows)

@app.route("/complaints", methods=["GET", "POST"])
@login_required
def complaints():
    db = get_db()
    if request.method == "POST":
        card = "TN-1001" if session["role"] == "beneficiary" else request.form.get("card_number", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        if card and category and description:
            db.execute("INSERT INTO complaints(card_number,category,description,status,created_at) VALUES(?,?,?,'Open',?)",
                       (card, category, description, datetime.now().strftime("%Y-%m-%d %H:%M")))
            db.commit()
            flash("Complaint submitted successfully.", "success")
            return redirect(url_for("complaints"))
        flash("Please complete all complaint fields.", "error")
    if session["role"] == "beneficiary":
        rows = db.execute("SELECT * FROM complaints WHERE card_number='TN-1001' ORDER BY id DESC").fetchall()
    else:
        rows = db.execute("SELECT * FROM complaints ORDER BY id DESC").fetchall()
    return render_template("complaints.html", rows=rows, beneficiary_rows=db.execute("SELECT * FROM beneficiaries ORDER BY name").fetchall())

@app.route("/complaints/<int:complaint_id>/status", methods=["POST"])
@login_required
@roles_required("admin", "operator")
def complaint_status(complaint_id):
    status = request.form.get("status", "")
    if status not in ("Open", "In Progress", "Resolved"):
        flash("Invalid status.", "error")
    else:
        db = get_db()
        db.execute("UPDATE complaints SET status=? WHERE id=?", (status, complaint_id))
        db.commit()
        flash("Complaint status updated.", "success")
    return redirect(url_for("complaints"))

@app.route("/reports")
@login_required
@roles_required("admin", "operator")
def reports():
    db = get_db()
    total_distributed = db.execute("SELECT COALESCE(SUM(quantity_kg),0) FROM transactions").fetchone()[0]
    by_item = db.execute("""SELECT commodity, SUM(quantity_kg) AS total FROM transactions
                            GROUP BY commodity ORDER BY commodity""").fetchall()
    return render_template("reports.html", total_distributed=total_distributed, by_item=by_item)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
