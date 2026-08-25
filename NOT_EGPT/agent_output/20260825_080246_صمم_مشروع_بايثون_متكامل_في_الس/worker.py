"""
worker.py
========
كلاس Worker بيشتغل بـ threading.
- كل Worker ليه loop خاص بيه بيـ claim مهمة من الـ Storage، ينفّذها، يحدّث حالتها.
- لو المهمة فشلت، بيرجّعها للـ PENDING مع زيادة retries (حتى الـ max_retries).
- مستفيد من الـ Circuit Breaker: لو الدائرة OPEN، الـ worker بيستنى بدل ما يحاول.
"""

from __future__ import annotations

import threading
import time
import traceback
from typing import Optional

from circuit_breaker import CircuitBreaker, CircuitOpenError
from storage import Storage
from task import Task, TaskStatus


class Worker:
    def __init__(
        self,
        worker_id: str,
        storage: Storage,
        breaker: CircuitBreaker,
        poll_interval: float = 0.05,
        sleep_on_empty: float = 0.05,
    ) -> None:
        self.worker_id = worker_id
        self.storage = storage
        self.breaker = breaker
        self.poll_interval = poll_interval
        self.sleep_on_empty = sleep_on_empty

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ---------- control ----------
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name=f"Worker-{self.worker_id}", daemon=True
        )
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    # ---------- loop ----------
    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                processed = self.process_once()
            except Exception:  # noqa: BLE001
                # أي استثناء غير متوقّع داخل الـ worker ما يوقّفش الـ loop
                traceback.print_exc()
                processed = False

            if not processed:
                # مفيش مهام → نام شوية
                self._stop_event.wait(self.sleep_on_empty)
            else:
                self._stop_event.wait(self.poll_interval)

    def process_once(self) -> bool:
        """بنحاول نـ claim مهمة ونشغّلها. بيرجع True لو اتعالجت مهمة."""
        if self.breaker.state.value == "OPEN":
            return False

        task = self.storage.claim_next()
        if task is None:
            return False

        try:
            result = self.breaker.call(task.execute)
        except CircuitOpenError:
            # رجّع المهمة للـ PENDING عشان يحاول worker تاني بعد reset_timeout
            task.status = TaskStatus.PENDING
            self.storage.update(task)
            return False
        except Exception as exc:  # noqa: BLE001
            task.mark_failed(exc)
            self.storage.update(task)
            return True

        task.mark_success(result)
        self.storage.update(task)
        return True
