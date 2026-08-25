# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Runtime — Provider-Specific Error Parsing
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §6.2 (runtime/errors.*)
         §9 "provider-specific error parsing"

BOUNDARY
--------
This module handles the *runtime* half of error handling: pulling the app code
out of a raw HTTP/SSE response. The *normalization* half (mapping to the 12
categories of §14) lives in the package-level ../errors.py, which §6.2 lists
separately. This file deliberately does not duplicate that mapping — it
extracts, then delegates.
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .. import errors as normalized

# App codes that the reference implementation recovers from — 01.06:798
RECOVERABLE_CODES = frozenset({164019, 164002, 164003})


def extract_app_code(response: Any) -> Optional[int]:
    """
    Pull the JSON `code` out of a response body.

    Required because NoteGPT returns application errors with HTTP 200
    (CORRECTIONS.md §8), so the status line reveals nothing.
    """
    try:
        body = response.json()
    except Exception:
        return None
    if not isinstance(body, dict):
        return None
    code = body.get("code")
    try:
        return int(code)
    except (TypeError, ValueError):
        return None


def is_recoverable_code(code: Optional[int]) -> bool:
    """True when identity rotation + retry is the documented response."""
    return code in RECOVERABLE_CODES if code is not None else False


def parse_response(response: Any) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Inspect a completed HTTP response.

    Returns (ok, normalized_error). `ok` is True only when the body carries the
    real success sentinel 100000 (CORRECTIONS.md §3 — never 0).
    """
    try:
        body = response.json()
    except Exception:
        body = None

    status = getattr(response, "status_code", None)

    if body and isinstance(body, dict) and "code" in body:
        if normalized.is_success_code(body.get("code")):
            return True, None
        return False, normalized.normalize_error(http_status=status, body=body).to_dict()

    if status is not None and status >= 400:
        return False, normalized.normalize_error(http_status=status).to_dict()

    # No app code and a non-error status: streaming endpoints answer this way.
    return True, None


def parse_stream_error(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize an SSE event that carries failure semantics, else None."""
    etype = event.get("type")
    if etype in normalized.STREAM_ERROR_EVENTS:
        return normalized.normalize_error(stream_event=etype).to_dict()

    code = event.get("code")
    if code is not None and not normalized.is_success_code(code):
        return normalized.normalize_error(body={"code": code}).to_dict()

    return None
