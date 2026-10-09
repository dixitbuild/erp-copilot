"""SQLite database seeded from the dummy data, with a read-only, table-restricted query helper."""

import os
import re
import sqlite3
from pathlib import Path

from erp_copilot.data.dummy_data import PURCHASE_ORDERS, SALES_ORDERS, WORK_ORDERS

DEFAULT_DB_PATH = Path(__file__).resolve().parents[3] / "erp.db"
DEFAULT_ALLOWED_TABLES = ("sales_orders", "purchase_orders", "work_orders")
MAX_ROWS = 100

SCHEMA = """
CREATE TABLE IF NOT EXISTS sales_orders (
    id TEXT PRIMARY KEY, customer TEXT, item TEXT, quantity INTEGER,
    total_amount REAL, status TEXT, order_date TEXT);
CREATE TABLE IF NOT EXISTS purchase_orders (
    id TEXT PRIMARY KEY, supplier TEXT, item TEXT, quantity INTEGER,
    total_amount REAL, status TEXT, expected_date TEXT);
CREATE TABLE IF NOT EXISTS work_orders (
    id TEXT PRIMARY KEY, product TEXT, quantity INTEGER, assigned_to TEXT,
    status TEXT, due_date TEXT);
"""


def db_path() -> Path:
    return Path(os.environ.get("ERP_DB_PATH", DEFAULT_DB_PATH))


def allowed_tables() -> tuple[str, ...]:
    raw = os.environ.get("ERP_ALLOWED_TABLES")
    return tuple(t.strip() for t in raw.split(",") if t.strip()) if raw else DEFAULT_ALLOWED_TABLES


def init_db() -> None:
    """Create tables and seed the dummy data if the database is empty."""
    with sqlite3.connect(db_path()) as conn:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM sales_orders").fetchone()[0]:
            return
        for table, orders in (
            ("sales_orders", SALES_ORDERS),
            ("purchase_orders", PURCHASE_ORDERS),
            ("work_orders", WORK_ORDERS),
        ):
            for order in orders:
                row = order.model_dump(mode="json")
                cols = ", ".join(row)
                marks = ", ".join("?" for _ in row)
                conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", list(row.values()))


def _connect_readonly() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db_path()}?mode=ro", uri=True)
    allowed = set(allowed_tables())

    def authorizer(action, arg1, arg2, db_name, source):
        if action == sqlite3.SQLITE_SELECT or action == sqlite3.SQLITE_FUNCTION:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ:
            return sqlite3.SQLITE_OK if arg1 in allowed else sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_DENY

    conn.set_authorizer(authorizer)
    return conn


def describe_table(table: str) -> list[dict]:
    if table not in allowed_tables():
        raise ValueError(f"Table '{table}' is not available. Allowed tables: {', '.join(allowed_tables())}")
    with sqlite3.connect(db_path()) as conn:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [{"column": r[1], "type": r[2], "primary_key": bool(r[5])} for r in rows]


def run_select(sql: str) -> dict:
    statement = sql.strip().rstrip(";").strip()
    if ";" in statement or not re.match(r"(?is)^\s*(select|with)\b", statement):
        raise ValueError("Only a single read-only SELECT statement is allowed.")
    conn = _connect_readonly()
    try:
        cursor = conn.execute(statement)
        columns = [d[0] for d in cursor.description or []]
        rows = cursor.fetchmany(MAX_ROWS + 1)
    except sqlite3.Error as exc:
        raise ValueError(f"Query failed: {exc}") from exc
    finally:
        conn.close()
    return {
        "columns": columns,
        "rows": [list(r) for r in rows[:MAX_ROWS]],
        "truncated": len(rows) > MAX_ROWS,
    }
