import sqlite3
from pathlib import Path

DB_PATH = str(Path(__file__).with_name("incidents.db"))


def _run(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
        conn.commit()
        return rows
    finally:
        conn.close()


def init():
    _run("""CREATE TABLE IF NOT EXISTS incidents (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              paused_at TEXT NOT NULL,
              resumed_at TEXT,
              error_rate REAL,
              reason TEXT)""")


def open_incident(paused_at, error_rate, reason):
    _run("INSERT INTO incidents (paused_at, error_rate, reason) VALUES (?, ?, ?)",
         (paused_at, error_rate, reason))


def close_incident(resumed_at):
    _run("""UPDATE incidents SET resumed_at = ?
            WHERE id = (SELECT id FROM incidents WHERE resumed_at IS NULL ORDER BY id DESC LIMIT 1)""",
         (resumed_at,))


def list_incidents(limit=100):
    rows = _run("SELECT * FROM incidents ORDER BY id DESC LIMIT ?", (limit,))
    return [dict(r) for r in rows]