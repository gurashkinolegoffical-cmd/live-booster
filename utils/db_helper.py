# utils/db_helper.py
import sqlite3
import os
from datetime import datetime

class DatabaseHelper:
    def __init__(self, db_path="live_booster.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            minutes INTEGER NOT NULL
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS streak (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            days INTEGER NOT NULL DEFAULT 0
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS calculator_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            income_text TEXT NOT NULL DEFAULT '',
            shifts_text TEXT NOT NULL DEFAULT '1',
            day REAL NOT NULL DEFAULT 0,
            week REAL NOT NULL DEFAULT 0,
            month REAL NOT NULL DEFAULT 0,
            year REAL NOT NULL DEFAULT 0,
            five_years REAL NOT NULL DEFAULT 0
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            username TEXT NOT NULL DEFAULT 'игрок'
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        )''')
        # Заполним таблицы значениями по умолчанию, если они пусты
        cursor.execute("INSERT OR IGNORE INTO streak (id, days) VALUES (1, 0)")
        cursor.execute("INSERT OR IGNORE INTO calculator_state (id) VALUES (1)")
        cursor.execute("INSERT OR IGNORE INTO profile (id, username) VALUES (1, 'игрок')")
        # Дефолтные ежедневные задачи, если таблица пуста
        cursor.execute("SELECT COUNT(*) FROM daily_tasks")
        if cursor.fetchone()[0] == 0:
            default_tasks = [
                "Зайти в игру и отметиться в daily bonus",
                "Отработать смену на автобусе / такси",
                "Проверить почту и ответить на письма",
                "Заглянуть в бизнес (если есть) – собрать прибыль",
                "Пообщаться с фракцией / друзьями",
            ]
            for task in default_tasks:
                cursor.execute("INSERT INTO daily_tasks (text, active) VALUES (?, 1)", (task,))
        self.conn.commit()

    # ---------- Reminders ----------
    def get_reminders(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, text, date, time, active FROM reminders ORDER BY id")
        rows = cursor.fetchall()
        return [{"id": r[0], "text": r[1], "date": r[2], "time": r[3], "active": bool(r[4])} for r in rows]

    def add_reminder(self, text, date, time, active=True):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO reminders (text, date, time, active) VALUES (?, ?, ?, ?)",
                       (text, date, time, int(active)))
        self.conn.commit()
        return cursor.lastrowid

    def update_reminder(self, reminder_id, active):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE reminders SET active = ? WHERE id = ?", (int(active), reminder_id))
        self.conn.commit()

    def delete_reminder(self, reminder_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        self.conn.commit()

    # ---------- Sessions ----------
    def add_session(self, start_time, end_time, minutes):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO sessions (start_time, end_time, minutes) VALUES (?, ?, ?)",
                       (start_time, end_time, minutes))
        self.conn.commit()

    def get_sessions(self, limit=10):
        cursor = self.conn.cursor()
        cursor.execute("SELECT start_time, end_time, minutes FROM sessions ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [{"start": r[0], "end": r[1], "minutes": r[2]} for r in rows]

    # ---------- Streak ----------
    def get_streak_days(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT days FROM streak WHERE id = 1")
        row = cursor.fetchone()
        return row[0] if row else 0

    def set_streak_days(self, days):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE streak SET days = ? WHERE id = 1", (days,))
        self.conn.commit()

    # ---------- Calculator State ----------
    def get_calculator_state(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT income_text, shifts_text, day, week, month, year, five_years FROM calculator_state WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return {
                "income_text": row[0],
                "shifts_text": row[1],
                "day": row[2],
                "week": row[3],
                "month": row[4],
                "year": row[5],
                "five_years": row[6]
            }
        return {"income_text": "", "shifts_text": "1", "day": 0, "week": 0, "month": 0, "year": 0, "five_years": 0}

    def set_calculator_state(self, state):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE calculator_state SET income_text=?, shifts_text=?, day=?, week=?, month=?, year=?, five_years=? WHERE id=1",
                       (state["income_text"], state["shifts_text"], state["day"], state["week"], state["month"], state["year"], state["five_years"]))
        self.conn.commit()

    # ---------- Profile ----------
    def get_username(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username FROM profile WHERE id = 1")
        row = cursor.fetchone()
        return row[0] if row else "игрок"

    def set_username(self, username):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE profile SET username = ? WHERE id = 1", (username,))
        self.conn.commit()

    # ---------- Daily Tasks ----------
    def get_daily_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, text, active FROM daily_tasks ORDER BY id")
        rows = cursor.fetchall()
        return [{"id": r[0], "text": r[1], "active": bool(r[2])} for r in rows]

    def update_daily_task(self, task_id, active):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE daily_tasks SET active = ? WHERE id = ?", (int(active), task_id))
        self.conn.commit()

    def add_daily_task(self, text):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO daily_tasks (text, active) VALUES (?, 1)", (text,))
        self.conn.commit()

    def delete_daily_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM daily_tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()