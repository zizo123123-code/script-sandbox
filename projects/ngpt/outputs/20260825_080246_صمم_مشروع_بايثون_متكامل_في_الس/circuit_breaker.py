"""
circuit_breaker.py
==================
نظام Circuit Breaker بسيط بيمنع انهيار السيرفر لما مهمة تقع بشكل متكرر.
- CLOSED  : الدائرة شغّالة طبيعي
- OPEN    : الدائرة مفتوحة، أي استدعاء بيقع فوراً
- HALF_OPEN: بنسمح باستدعاء واحد تجريبي عشان نقرر نقفل تاني ولا نرجّع CLOSED
"""

from __future__ import annotations

import threading
import time
from enum import Enum
from typing import Callable, Any


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitOpenError(RuntimeError):
    """بتترفع لما الـ breaker يكون OPEN والمستدعي يحاول ينفّذ الدالة."""


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 3,
        reset_timeout: float = 5.0,
        expected_exceptions: tuple = (Exception,),
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.expected_exceptions = expected_exceptions

        self._state = CircuitState.CLOSED
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = threading.Lock()

    # ---------- state ----------
    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._state

    @property
    def failures(self) -> int:
        with self._lock:
            return self._failures

    def _set_state(self, new_state: CircuitState) -> None:
        self._state = new_state
        if new_state == CircuitState.OPEN:
            self._opened_at = time.monotonic()
        elif new_state == CircuitState.CLOSED:
            self._failures = 0
            self._opened_at = None
        # HALF_OPEN: بنخلي العدّاد زي ما هو عشان الاستدعاء التجريبي يحدّد

    def _maybe_transition_to_half_open(self) -> None:
        if (
            self._state == CircuitState.OPEN
            and self._opened_at is not None
            and (time.monotonic() - self._opened_at) >= self.reset_timeout
        ):
            self._state = CircuitState.HALF_OPEN

    # ---------- public API ----------
    def call(self, func: Callable[..., Any], *args, **kwargs):
        with self._lock:
            self._maybe_transition_to_half_open()
            if self._state == CircuitState.OPEN:
                raise CircuitOpenError("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
        except self.expected_exceptions as exc:
            self._on_failure()
            raise
        else:
            self._on_success()
            return result

    # ---------- internals ----------
    def _on_success(self) -> None:
        with self._lock:
            self._failures = 0
            # لو HALF_OPEN ونجحت، نرجّع CLOSED
            if self._state in (CircuitState.HALF_OPEN, CircuitState.OPEN):
                self._set_state(CircuitState.CLOSED)

    def _on_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._state == CircuitState.HALF_OPEN:
                # الاستدعاء التجريبي وقع → نرجّع OPEN فوراً
                self._set_state(CircuitState.OPEN)
            elif (
                self._state == CircuitState.CLOSED
                and self._failures >= self.failure_threshold
            ):
                self._set_state(CircuitState.OPEN)

    # ---------- helpers للاختبارات ----------
    def force_open(self) -> None:
        with self._lock:
            self._set_state(CircuitState.OPEN)

    def force_close(self) -> None:
        with self._lock:
            self._set_state(CircuitState.CLOSED)
