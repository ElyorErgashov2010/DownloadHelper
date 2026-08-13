"""Yuklab olish tarixi uchun SQLite asosidagi vazifa menejeri."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DB_DIR = Path.home() / ".downloader_helper"
DB_PATH = DB_DIR / "tasks.db"


@dataclass
class Task:
    id: int | None = None
    name: str = ""
    command: str = ""
    status: str = "Pending"  # Pending, Downloading, Uploading, Done, Failed
    destination_type: str = "local"  # local or s3
    destination_path: str = ""
    created_at: str = ""
    log_text: str = ""


class TaskManager:
    def __init__(self):
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(DB_PATH))
        self._conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                command TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                destination_type TEXT NOT NULL DEFAULT 'local',
                destination_path TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                log_text TEXT NOT NULL DEFAULT ''
            )
        """)
        self._conn.commit()

    def create_task(self, task: Task) -> Task:
        task.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = self._conn.execute(
            """INSERT INTO tasks (name, command, status, destination_type,
               destination_path, created_at, log_text)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (task.name, task.command, task.status, task.destination_type,
             task.destination_path, task.created_at, task.log_text),
        )
        self._conn.commit()
        task.id = cur.lastrowid
        return task

    def update_status(self, task_id: int, status: str):
        self._conn.execute(
            "UPDATE tasks SET status = ? WHERE id = ?", (status, task_id)
        )
        self._conn.commit()

    def append_log(self, task_id: int, text: str):
        self._conn.execute(
            "UPDATE tasks SET log_text = log_text || ? WHERE id = ?",
            (text, task_id),
        )
        self._conn.commit()

    def save_log(self, task_id: int, full_text: str):
        """Vazifa logini to'liq matn bilan qayta yozadi."""
        self._conn.execute(
            "UPDATE tasks SET log_text = ? WHERE id = ?",
            (full_text, task_id),
        )
        self._conn.commit()

    def get_log(self, task_id: int) -> str:
        row = self._conn.execute(
            "SELECT log_text FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return row["log_text"] if row else ""

    def get_all_tasks(self) -> list[Task]:
        rows = self._conn.execute(
            "SELECT * FROM tasks ORDER BY id DESC"
        ).fetchall()
        return [self._row_to_task(r) for r in rows]

    def get_task(self, task_id: int) -> Task | None:
        row = self._conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return self._row_to_task(row) if row else None

    def delete_task(self, task_id: int):
        self._conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self._conn.commit()

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            name=row["name"],
            command=row["command"],
            status=row["status"],
            destination_type=row["destination_type"],
            destination_path=row["destination_path"],
            created_at=row["created_at"],
            log_text=row["log_text"],
        )
