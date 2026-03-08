import sqlite3
import json
from pathlib import Path
from datetime import datetime
import config_manager


def _db_path() -> Path:
    rel = config_manager.get_cache("sqlite_path", "cache.db")
    return Path(__file__).parent / rel


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()))
    conn.row_factory = sqlite3.Row
    return conn


def initialize():
    conn = _connect()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS holiday_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            holidays_json TEXT NOT NULL,
            cached_at TEXT NOT NULL,
            UNIQUE(country, year, month)
        )
    """)
    conn.commit()
    conn.close()


def store(country: str, year: int, month: int, holidays: list):
    conn = _connect()
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute("""
        INSERT OR REPLACE INTO holiday_cache (country, year, month, holidays_json, cached_at)
        VALUES (?, ?, ?, ?, ?)
    """, (country.upper(), year, month, json.dumps(holidays), now))
    conn.commit()
    conn.close()


def fetch(country: str, year: int, month: int) -> list | None:
    expire_days = config_manager.get_cache("expire_days", 7)
    conn = _connect()
    c = conn.cursor()
    c.execute("""
        SELECT holidays_json, cached_at FROM holiday_cache
        WHERE country = ? AND year = ? AND month = ?
    """, (country.upper(), year, month))
    row = c.fetchone()
    conn.close()
    if row is None:
        return None
    cached_at = datetime.fromisoformat(row["cached_at"])
    age = (datetime.utcnow() - cached_at).days
    if age > expire_days:
        return None
    return json.loads(row["holidays_json"])


def clear_expired():
    expire_days = config_manager.get_cache("expire_days", 7)
    conn = _connect()
    c = conn.cursor()
    c.execute("""
        DELETE FROM holiday_cache
        WHERE (julianday('now') - julianday(cached_at)) > ?
    """, (expire_days,))
    conn.commit()
    conn.close()


def clear_all():
    conn = _connect()
    c = conn.cursor()
    c.execute("DELETE FROM holiday_cache")
    conn.commit()
    conn.close()


initialize()
