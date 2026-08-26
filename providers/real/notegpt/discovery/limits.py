# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Discovery — Rate Limits & Quotas
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §12
SOURCE : inventory/notegpt/CORRECTIONS.md §7

30 §12 requires translating real provider limits into the normalized states:
    available · limited · cooldown_until · unknown

WHAT WAS CORRECTED (CORRECTIONS.md §7)
--------------------------------------
The original limits.md presented a full table of hard numbers. Almost all of
them had no source:

    "50-100 credits/day"   -> UNKNOWN (cited line 518, which is unrelated)
    "10 requests/minute"   -> UNKNOWN (zero 429 responses in 916 entries)
    "60s cooldown"         -> UNKNOWN
    "resets at 00:00 UTC"  -> UNKNOWN
    "64k-128k context"     -> UNKNOWN

Reporting "unknown" is the correct engineering answer here: a fabricated
budget would make the router throttle against a number that does not exist.
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict, Optional

# T-01 — single source of truth. The value was previously declared twice
# (config.py and here) with no link between them, so the two could silently
# diverge. `config.py` is the origin (it imports nothing internal); this module
# re-exports the same object so `limits_mod.AUTO_CONTINUE_LIMIT` and
# `config.AUTO_CONTINUE_LIMIT` can never disagree.
from ..config import AUTO_CONTINUE_LIMIT  # noqa: F401  (re-exported)

# Normalized states — 30 §12
STATE_AVAILABLE = "available"
STATE_LIMITED = "limited"
STATE_COOLDOWN = "cooldown_until"
STATE_UNKNOWN = "unknown"

# --- CONFIRMED limits -------------------------------------------------------
QUOTA_EXHAUSTED_CODE = 164019     # HAR x14 · handled 01.06:798
MAX_ATTACHED_SOURCES = 5          # 01.06:106
REQUEST_TIMEOUT_SECONDS = 120     # 01.06:103

CONFIRMED_LIMITS: Dict[str, Any] = {
    "quota_exhausted_code": QUOTA_EXHAUSTED_CODE,
    "auto_continue_limit": AUTO_CONTINUE_LIMIT,
    "max_attached_sources": MAX_ATTACHED_SOURCES,
    "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
}

# --- UNKNOWN limits (each was a fabricated value in the original docs) ------
UNKNOWN_LIMITS: Dict[str, str] = {
    "daily_quota": "no evidence; '50-100 credits' cited an unrelated line",
    "requests_per_minute": "no evidence; zero HTTP 429 in 916 HAR entries",
    "cooldown_seconds": "no evidence",
    "quota_reset_time": "no evidence",
    "context_window": "no evidence; varies per model, none documented",
    "max_file_size": "no evidence; '50 MB' was unsourced",
    "concurrency": "no evidence",
    "agent_tool_ceiling": "agent_tool_limit event exists; numeric cap unknown",
}


def get_limits() -> Dict[str, Any]:
    """Full limit picture, honest about what is not known."""
    return {
        "strategy": "provider_defined",
        "dimensions": ["account", "endpoint", "time_window"],
        "confirmed": dict(CONFIRMED_LIMITS),
        "unknown": dict(UNKNOWN_LIMITS),
        "note": (
            "Only quota exhaustion (code 164019) is observable. There is no "
            "documented numeric budget, so the platform must treat capacity "
            "as unknown and react to 164019 rather than pre-throttle."
        ),
    }


def normalize_limit_state(
    *,
    app_code: Optional[int] = None,
    cooldown_until: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Map an observed signal to a normalized rate-limit state — 30 §12.
    """
    if app_code == QUOTA_EXHAUSTED_CODE:
        return {
            "state": STATE_LIMITED,
            "reason": "plan_quota_exceeded",
            "provider_code": str(QUOTA_EXHAUSTED_CODE),
            "recovery": "rotate_identity",
            "retry_after_ms": None,     # reset window is UNKNOWN
        }
    if cooldown_until is not None:
        return {
            "state": STATE_COOLDOWN,
            "cooldown_until": cooldown_until,
            "reason": "explicit_cooldown",
        }
    if app_code is None:
        return {
            "state": STATE_UNKNOWN,
            "reason": "no_quota_signal_observed",
        }
    return {"state": STATE_AVAILABLE, "reason": "no_limit_signal"}


def should_auto_continue(continue_calls: int) -> bool:
    """Auto-continue budget — the one hard ceiling that IS evidenced (01.06:104)."""
    return continue_calls < AUTO_CONTINUE_LIMIT
