# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Account — Refresh  [IMPLEMENTED — single account]
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §8.2 (refreshAccount)
SOURCE : inventory/notegpt/CORRECTIONS.md §3 (code 164003 = "login expired")
         projects/ngpt/scripts/01.06 :495-521

This is the ONE account-lifecycle operation that genuinely exists. There is no
refresh-token endpoint, so "refresh" means a full re-login, triggered by app
code 164003 arriving with HTTP 200.
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict

from ..config import NoteGPTConfig
from ..runtime import auth as auth_mod

SUPPORTED = True
TRIGGER_CODES = frozenset({164003, 164002})   # "login expired" / auth failure


def refresh_account(config: NoteGPTConfig, scraper: Any = None) -> Dict[str, Any]:
    """Re-authenticate the single configured account."""
    token, error = auth_mod.refresh_session(config, scraper=scraper)
    if error:
        return {"refreshed": False, "state": "AUTH_EXPIRED", "error": error}
    return {"refreshed": True, "state": "READY", "has_token": bool(token)}


def should_refresh(app_code: Any) -> bool:
    """True when the observed app code means the session must be renewed."""
    try:
        return int(app_code) in TRIGGER_CODES
    except (TypeError, ValueError):
        return False
