# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Provider Health — Circuit Breaker
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §6.2, §13.2
SOURCE : inventory/notegpt/health.md §2 (heuristic) — CORRECTIONS.md §3

30 §13.2: "provider errors/timeouts increase -> provider health degrades ->
circuit breaker opens -> router skips provider temporarily."

A NOTE ON THRESHOLDS
--------------------
NoteGPT exposes no rate-limit or retry-after headers, and the observed HAR
contains ZERO 429/503/504 responses (CORRECTIONS.md §3). So no provider-derived
threshold exists. The values below are PLATFORM POLICY defaults, labelled as
such — they are not presented as measured provider behavior.
================================================================================
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

CLOSED = "closed"        # traffic flows
OPEN = "open"            # traffic blocked
HALF_OPEN = "half_open"  # trial request allowed

# Platform policy defaults — NOT provider-derived (no evidence exists).
DEFAULT_FAILURE_THRESHOLD = 3
DEFAULT_RECOVERY_SECONDS = 60
THRESHOLD_SOURCE = "platform_policy_default"


@dataclass
class CircuitBreaker:
    """Per-provider breaker. Distinguishes provider faults from account faults."""

    failure_threshold: int = DEFAULT_FAILURE_THRESHOLD
    recovery_seconds: int = DEFAULT_RECOVERY_SECONDS
    state: str = CLOSED
    consecutive_failures: int = 0
    opened_at: Optional[float] = None
    history: list = field(default_factory=list)

    # 30 §13.2 — account-level problems must NOT open the provider breaker.
    ACCOUNT_LEVEL_CATEGORIES = frozenset({
        "auth_expired", "invalid_credential", "quota_exceeded",
    })

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.state = CLOSED
        self.opened_at = None
        self.history.append(("success", time.time()))

    def record_failure(self, category: Optional[str] = None) -> str:
        """Record a failure. Account-scoped categories are ignored by design."""
        if category in self.ACCOUNT_LEVEL_CATEGORIES:
            self.history.append(("account_failure_ignored", time.time()))
            return self.state

        self.consecutive_failures += 1
        self.history.append((category or "provider_failure", time.time()))
        if self.consecutive_failures >= self.failure_threshold:
            self.state = OPEN
            self.opened_at = time.time()
        return self.state

    def allows_request(self) -> bool:
        if self.state == CLOSED:
            return True
        if self.state == OPEN:
            if self.opened_at and (time.time() - self.opened_at) >= self.recovery_seconds:
                self.state = HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN: allow one trial

    def snapshot(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "consecutive_failures": self.consecutive_failures,
            "opened_at": self.opened_at,
            "failure_threshold": self.failure_threshold,
            "recovery_seconds": self.recovery_seconds,
            "threshold_source": THRESHOLD_SOURCE,
        }
