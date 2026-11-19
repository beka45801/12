"""Всё, что связано с базой данных SQLite."""
import sqlite3
from datetime import datetime, date

from config import DB_PATH, TZ


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создаёт таблицы при первом запуске."""
    with db() as c:
        c.executescript(
            """
            -- Все записи доходов и расходов
            CREATE TABLE IF NOT EXISTS tx(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                kind TEXT NOT NULL,            -- income (доход) / expense (расход)
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                created_at TEXT NOT NULL,      -- дата и время: 2026-11-19 14:30:00
                day TEXT NOT NULL              -- только дата: 2026-11-19
            );
            CREATE INDEX IF NOT EXISTS idx_tx_user_day ON tx(user_id, day);

            -- Кто пользуется ботом (чтобы слать автоотчёт)
            CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY,
                chat_id INTEGER NOT NULL
            );

            -- Служебное: помним, за какой месяц отчёт уже отправлен
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
            """
        )


def register_user(user_id: int, chat_id: int):
    with db() as c:
        c.execute("INSERT OR REPLACE INTO users(user_id, chat_id) VALUES(?,?)", (user_id, chat_id))


def get_users():
    with db() as c:
        return c.execute("SELECT * FROM users").fetchall()


def add_tx(user_id: int, kind: str, amount: float, category: str):
    now = datetime.now(TZ)
    with db() as c:
        c.execute(
            "INSERT INTO tx(user_id, kind, amount, category, created_at, day) VALUES(?,?,?,?,?,?)",
            (user_id, kind, amount, category,
             now.strftime("%Y-%m-%d %H:%M:%S"), now.strftime("%Y-%m-%d")),
        )


def get_tx(user_id: int, start: date, end: date):
    """Все записи пользователя между двумя датами включительно."""
    with db() as c:
        return c.execute(
            "SELECT * FROM tx WHERE user_id=? AND day BETWEEN ? AND ? ORDER BY created_at",
            (user_id, start.isoformat(), end.isoformat()),
        ).fetchall()


def delete_last(user_id: int):
    with db() as c:
        row = c.execute(
            "SELECT * FROM tx WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,)
        ).fetchone()
        if row:
            c.execute("DELETE FROM tx WHERE id=?", (row["id"],))
        return row


def meta_get(key: str):
    with db() as c:
        row = c.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None


def meta_set(key: str, value: str):
    with db() as c:
        c.execute("INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)", (key, value))
