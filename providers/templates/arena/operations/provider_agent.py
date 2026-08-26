# -*- coding: utf-8 -*-
"""Non-executable provider-agent operation for the Arena.ai template."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .. import errors as err


def run_provider_agent(request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return the normalized disabled error without making a network call."""
    return {"error": err.normalize_error(category=err.PROVIDER_DISABLED).to_dict()}
