"""
queue.py
=======
TaskQueue = Distributed Task Queue مصغّر.
- بيغلف الـ Storage + الـ Circuit Breaker + كذا Worker شغّالين في الـ background.
- بيديك API بسيط: enqueue()، start_workers()، stop_workers()، wait_until_done().
"""

from __future__ import annotations

import time
from typing import List, Optional

from circuit_breaker import CircuitBreaker
from storage import Storage
from task import Task, TaskStatus
from worker import Worker


class TaskQueue:
    def __init__(
        self,
        db_path: str = ":memory:",
        num_workers: int = 2,
        failure_threshold: int = 3,
        reset_timeout: float = 1.0,
        poll_interval: float = 0.02,
        sleep_on_empty: float = 0.02,
        expected_exceptions: tuple = (Exception,),
    ) -> None:
        self.storage = Storage(db_path=db_path)
        self.breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            reset_timeout=reset_timeout,
            expected_exceptions=expected_exceptions,
        )
        self.num_workers = num_workers
        self.poll_interval = poll_interval
        self.sleep_on_empty = sleep_on_empty

        self._workers: List[Worker] = []

    # ---------- task API ----------
    def enqueue(self, task: Task) -> Task:
        self.storage.enqueue(task)
        return task

    def enqueue_many(self, tasks: List[Task]) -> List[Task]:
        for t in tasks:
            self.storage.enqueue(t)
        return tasks

    def get(self, task_id: str) -> Optional[Task]:
        return self.storage.get(task_id)

    def count(self, status: TaskStatus) -> int:
        return self.storage.count_by_status(status)

    # ---------- workers ----------
    def start_workers(self) -> None:
        if self._workers:
            return
        for i in range(self.num_workers):
            w = Worker(
                worker_id=str(i),
                storage=self.storage,
                breaker=self.breaker,
                poll_interval=self.poll_interval,
                sleep_on_empty=self.sleep_on_empty,
            )
            self._workers.append(w)
            w.start()

    def stop_workers(self, timeout: float = 2.0) -> None:
        for w in self._workers:
            w.stop(timeout=timeout)
        self._workers.clear()

    # ---------- helpers ----------
    def wait_until_done(
        self,
        timeout: float = 10.0,
        poll: float = 0.02,
    ) -> bool:
        """
        بيسنّى لحد ما مفيش مهام PENDING/RUNNING، أو لحد ما الوقت اللي حددناه يخلّص.
        بترجع True لو خلصنا قبل الـ timeout.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            pending = self.count(TaskStatus.PENDING)
            running = self.count(TaskStatus.RUNNING)
            if pending == 0 and running == 0:
                return True
            time.sleep(poll)
        return False

    def shutdown(self) -> None:
        self.stop_workers()
        self.storage.close()
