import os
import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

# Resolve project root relative to this file (database/db.py -> project root).
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(_PROJECT_ROOT, "expense_tracker.db")

CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]


def _resolve_path(db_path=None):
    return db_path if db_path is not None else DATABASE_PATH


def get_db(db_path=None):
    """Open a SQLite connection with row_factory and FK enforcement."""
    conn = sqlite3.connect(_resolve_path(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=None):
    """Create both tables if they do not already exist."""
    conn = get_db(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _sample_expense_dates():
    """Return 8 dates spread across the current month (YYYY-MM-DD)."""
    today = date.today()
    year, month = today.year, today.month
    # Last day of the current month.
    if month == 12:
        last_day = 31
    elif month in (1, 3, 5, 7, 8, 10):
        last_day = 31
    elif month == 2:
        last_day = 29
    else:
        last_day = 30

    desired_days = [2, 5, 9, 12, 15, 18, 22, 26]
    days = []
    for d in desired_days:
        days.append(min(d, last_day))
    # De-duplicate while preserving order just in case.
    seen = set()
    result = []
    for d in days:
        if d not in seen:
            seen.add(d)
            result.append(f"{year:04d}-{month:02d}-{d:02d}")
    # Pad if somehow fewer than 8.
    i = 1
    while len(result) < 8:
        day = min(i, last_day)
        iso = f"{year:04d}-{month:02d}-{day:02d}"
        if iso not in result:
            result.append(iso)
        i += 1
    return result[:8]


def _seed_expenses(conn, user_id):
    dates = _sample_expense_dates()
    expenses = [
        (user_id, 250.00, "Food", dates[0], "Groceries and vegetables"),
        (user_id, 45.50, "Transport", dates[1], "Metro fare"),
        (user_id, 1200.00, "Bills", dates[2], "Electricity bill"),
        (user_id, 350.00, "Health", dates[3], "Pharmacy"),
        (user_id, 499.00, "Entertainment", dates[4], "Movie tickets"),
        (user_id, 1800.00, "Shopping", dates[5], "Clothing"),
        (user_id, 60.00, "Other", dates[6], "Miscellaneous"),
        (user_id, 320.00, "Food", dates[7], "Restaurant dinner"),
    ]
    conn.executemany(
        """
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        expenses,
    )


def seed_db(db_path=None):
    """Insert demo data once; no-op if users already exist."""
    conn = get_db(db_path)
    try:
        row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
        if row is not None and row["c"] > 0:
            return
        cur = conn.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = cur.lastrowid
        _seed_expenses(conn, user_id)
        conn.commit()
    finally:
        conn.close()
