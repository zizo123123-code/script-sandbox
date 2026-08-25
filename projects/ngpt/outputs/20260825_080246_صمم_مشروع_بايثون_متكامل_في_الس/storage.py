"""
storage.py
=========
طبقة التخزين (SQLite) للمهام.
- enqueue(task)        : تضيف مهمة في جدول المهام
- claim_next()         : بتجيب أقدم مهمة PENDING (Atomic update) عشان الـ workers
- update(task)         : بتحدّث حالة المهمة (SUCCESS / FAILED / RUNNING)
- list_by_status(...)  : فلترة
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from typing import Iterator, List, Optional

from task import Task, TaskStatus


SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    args        TEXT NOT NULL DEFAULT '[]',
    kwargs      TEXT NOT NULL DEFAULT '{}',
    priority    INTEGER NOT NULL DEFAULT 5,
    max_retries INTEGER NOT NULL DEFAULT 3,
    retries     INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'PENDING',
    result      TEXT,
    error       TEXT,
    created_at  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_status_priority
    ON tasks (status, priority, created_at);
"""


class Storage:
    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._lock = threading.RLock()
        # check_same_thread=False عشان نقدر نشارك الاتصال بين الـ threads،
        # والـ lock في كل عملية بيحمي من race conditions.
        self._conn = sqlite3.connect(
            db_path, check_same_thread=False, isolation_level=None
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        with self._lock:
            self._conn.executescript(SCHEMA)

    @contextmanager
    def _cursor(self) -> Iterator[sqlite3.Cursor]:
        with self._lock:
            cur = self._conn.cursor()
            try:
                yield cur
            finally:
                cur.close()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ---------- CRUD ----------
    def enqueue(self, task: Task) -> None:
        data = task.to_dict()
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO tasks (
                    id, name, args, kwargs, priority, max_retries,
                    retries, status, result, error, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["name"],
                    json_dumps(data["args"]),
                    json_dumps(data["kwargs"]),
                    data["priority"],
                    data["max_retries"],
                    data["retries"],
                    data["status"],
                    data["result"],
                    data["error"],
                    data["created_at"],
                ),
            )

    def update(self, task: Task) -> None:
        data = task.to_dict()
        with self._cursor() as cur:
            cur.execute(
                """
                UPDATE tasks SET
                    name=?, args=?, kwargs=?, priority=?, max_retries=?,
                    retries=?, status=?, result=?, error=?
                WHERE id=?
                """,
                (
                    data["name"],
                    json_dumps(data["args"]),
                    json_dumps(data["kwargs"]),
                    data["priority"],
                    data["max_retries"],
                    data["retries"],
                    data["status"],
                    data["result"],
                    data["error"],
                    data["id"],
                ),
            )

    def get(self, task_id: str) -> Optional[Task]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            row = cur.fetchone()
            return _row_to_task(row) if row else None

    def claim_next(self) -> Optional[Task]:
        """Atomic claim: بنعمل UPDATE لصف واحد PENDING وبنرجّعه."""
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT id FROM tasks
                WHERE status='PENDING'
                ORDER BY priority ASC, created_at ASC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if row is None:
                return None
            task_id = row["id"]
            cur.execute(
                "UPDATE tasks SET status='RUNNING' WHERE id=?",
                (task_id,),
            )
            cur.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            return _row_to_task(cur.fetchone())

    def list_by_status(self, status: TaskStatus) -> List[Task]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM tasks WHERE status=? ORDER BY created_at ASC",
                (status.value,),
            )
            return [_row_to_task(r) for r in cur.fetchall()]

    def count_by_status(self, status: TaskStatus) -> int:
        with self._cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS c FROM tasks WHERE status=?",
                (status.value,),
            )
            return int(cur.fetchone()["c"])

    def reset(self) -> None:
        """بيمسح كل البيانات — مفيد جداً في الاختبارات."""
        with self._cursor() as cur:
            cur.execute("DELETE FROM tasks;")


# ---------- helpers ----------
def _row_to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        name=row["name"],
        args=tuple(json_loads(row["args"])),
        kwargs=json_loads(row["kwargs"]),
        priority=row["priority"],
        max_retries=row["max_retries"],
        retries=row["retries"],
        status=TaskStatus(row["status"]),
        result=row["result"],
        error=row["error"],
        created_at=row["created_at"],
    )


def json_dumps(obj) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False)


def json_loads(raw: str):
    import json

    return json.loads(raw) if raw else ([] if raw == "[]" else {})
