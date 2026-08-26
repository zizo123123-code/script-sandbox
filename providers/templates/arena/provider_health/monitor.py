# -*- coding: utf-8 -*-
"""Health contract for a disabled, non-functional provider template."""

from __future__ import annotations

from typing import Any, Dict


def health_check(scope: str = "provider", **kwargs: Any) -> Dict[str, Any]:
    """Never probe a network from a template; report the known state."""
    return {
        "state": "SUSPENDED",
        "scope": scope,
        "reason": "provider_template_disabled",
        "checked_live": False,
        "is_functional": False,
    }
