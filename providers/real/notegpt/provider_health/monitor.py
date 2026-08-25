# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Provider Health — Monitor
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §11
SOURCE : inventory/notegpt/CORRECTIONS.md §8 · health.md (endpoints corrected)

THE RULE THAT DEFINES THIS MODULE
---------------------------------
NoteGPT answers an expired session with:

    HTTP/1.1 200 OK
    {"code": 164003, "message": "login expired"}

CORRECTIONS.md §8: "you CANNOT rely on the HTTP status alone to detect session
expiry." Every probe here parses the JSON `code` and compares it to 100000.

CORRECTED ENDPOINTS (the original health.md had all three wrong)
    GET /api/v1/userinfo            not /api/v2/user/info
    GET /api/v2/plan-quota          not /api/v2/plan/quota
    GET /api/v2/user/quota-usage    was missing entirely
And the success sentinel is 100000, not the claimed `code: 0` — which appears
zero times in 916 HAR entries.
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .. import errors as err
from ..config import NoteGPTConfig

# Provider-wide states — 30 §11
HEALTHY = "HEALTHY"
DEGRADED = "DEGRADED"
UNAVAILABLE = "UNAVAILABLE"
SUSPENDED = "SUSPENDED"

# Account-level states — 30 §11
READY = "READY"
COOLDOWN = "COOLDOWN"
AUTH_EXPIRED = "AUTH_EXPIRED"
INVALID = "INVALID"

# health.md §2 — degradation heuristic (inference, not a provider signal)
DEGRADED_SUCCESS_RATE_THRESHOLD = 0.8
DEGRADED_WINDOW = 5


def _probe(config: NoteGPTConfig, endpoint_key: str, scraper: Any = None) -> Dict[str, Any]:
    """Run one GET probe and judge it by the app code, never the HTTP status."""
    from ..runtime import auth as auth_mod
    from ..runtime import request as request_mod

    scraper = scraper or request_mod.create_scraper()
    ctx = auth_mod.build_auth_context(config)

    try:
        response = scraper.get(
            config.url(endpoint_key),
            headers=ctx["headers"],
            cookies=ctx["cookies"],
            timeout=15,
        )
    except Exception as exc:
        return {"ok": False, "error": err.normalize_error(exc).to_dict()}

    try:
        body = response.json()
    except Exception:
        body = None

    if body and isinstance(body, dict):
        if err.is_success_code(body.get("code")):
            return {"ok": True, "body": body}
        return {
            "ok": False,
            "error": err.normalize_error(
                http_status=response.status_code, body=body
            ).to_dict(),
            "app_code": body.get("code"),
        }

    return {
        "ok": False,
        "error": err.normalize_error(http_status=response.status_code).to_dict(),
    }


def check_credential(config: NoteGPTConfig, scraper: Any = None) -> Dict[str, Any]:
    """
    Credential health — 30 §8.1 validateCredential().
    Probe: GET /api/v1/userinfo -> code == 100000
    """
    if not config.has_credentials:
        return {"valid": False, "state": INVALID, "reason": "no_credentials_configured"}

    result = _probe(config, "user_info", scraper=scraper)
    if result["ok"]:
        return {"valid": True, "state": READY, "checked_live": True}

    category = (result.get("error") or {}).get("category")
    state = AUTH_EXPIRED if category in {err.AUTH_EXPIRED, err.INVALID_CREDENTIAL} else INVALID
    return {
        "valid": False,
        "state": state,
        "checked_live": True,
        "error": result.get("error"),
    }


def check_quota(config: NoteGPTConfig, scraper: Any = None) -> Dict[str, Any]:
    """
    Quota probe: GET /api/v2/plan-quota -> code == 100000.

    The response's numeric budget fields are not documented anywhere, so this
    reports reachability + the raw payload and lets the caller interpret it,
    rather than asserting a "remaining_credit" field that may not exist.
    """
    result = _probe(config, "plan_quota", scraper=scraper)
    if result["ok"]:
        return {
            "available": "unknown",
            "reachable": True,
            "raw": result.get("body", {}).get("data"),
            "note": "Numeric quota fields are undocumented (CORRECTIONS.md §7).",
        }
    return {"available": False, "reachable": False, "error": result.get("error")}


def health_check(config: NoteGPTConfig, scope: str = "provider") -> Dict[str, Any]:
    """
    Provider health — 30 §11.

    "Do not confuse one account failed with the whole provider is down."
    An auth failure yields HEALTHY provider + AUTH_EXPIRED account.
    """
    checks: Dict[str, Any] = {}

    from ..runtime import request as request_mod

    try:
        scraper = request_mod.create_scraper()
    except ImportError:
        return {
            "state": UNAVAILABLE,
            "scope": scope,
            "reason": "cloudscraper_not_installed",
            "note": "notes.md §1 marks cloudscraper mandatory for TLS/JA3 match.",
        }

    # 1. endpoint reachability
    try:
        ping = scraper.get(config.base_url, timeout=10)
        checks["endpoint_available"] = getattr(ping, "status_code", None) == 200
    except Exception as exc:
        checks["endpoint_available"] = False
        checks["endpoint_error"] = err.normalize_error(exc).to_dict()

    # 2. credential validity
    credential = check_credential(config, scraper=scraper)
    checks["auth_valid"] = credential.get("valid", False)
    checks["account_state"] = credential.get("state")

    # 3. quota reachability
    if checks["auth_valid"]:
        quota = check_quota(config, scraper=scraper)
        checks["quota_available"] = quota.get("reachable", False)
        checks["quota_detail"] = quota
    else:
        checks["quota_available"] = "unknown"

    if not checks.get("endpoint_available"):
        provider_state = UNAVAILABLE
    elif not checks["auth_valid"]:
        provider_state = HEALTHY      # provider is fine; the account is not
    else:
        provider_state = HEALTHY

    return {
        "state": provider_state,
        "account_state": checks.get("account_state"),
        "scope": scope,
        "checks": checks,
        "checked_live": True,
        "note": (
            "Health is judged by JSON app code, not HTTP status: an expired "
            "session returns HTTP 200 with code 164003."
        ),
    }


def infer_state_from_history(successes: int, total: int) -> str:
    """
    health.md §2 — infer DEGRADED from the recent success rate.

    Marked as inference, not a provider signal: NoteGPT exposes no status
    endpoint, and zero 429/503/504 responses appear in the observed HAR.
    """
    if total <= 0:
        return SUSPENDED
    if total < DEGRADED_WINDOW:
        return HEALTHY
    return HEALTHY if (successes / total) >= DEGRADED_SUCCESS_RATE_THRESHOLD else DEGRADED
