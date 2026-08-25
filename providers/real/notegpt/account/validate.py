# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Account — Validate  [IMPLEMENTED — single account]
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §8.1 (validateCredential)
SOURCE : inventory/notegpt/CORRECTIONS.md §8

Probe: GET /api/v1/userinfo, judged by `code == 100000`.
The endpoint name was corrected from the original health.md claim of
/api/v2/user/info, and the success sentinel from `code: 0` (which never
appears) to 100000 (which appears 728 times).
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict

from ..config import NoteGPTConfig
from ..provider_health import monitor as monitor_mod

SUPPORTED = True


def validate_account(config: NoteGPTConfig, scraper: Any = None) -> Dict[str, Any]:
    """Validate the configured credential against the live provider."""
    return monitor_mod.check_credential(config, scraper=scraper)
