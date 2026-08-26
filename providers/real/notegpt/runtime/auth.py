# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Runtime — Authentication
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §9
SOURCE : inventory/notegpt/CORRECTIONS.md §1 (auth corrections)
         projects/ngpt/scripts/01.06 :495-521 (login_and_refresh_token)

CORRECTED FACTS (CORRECTIONS.md §1)
-----------------------------------
  * There is NO Clerk.  `grep -ci clerk` = 0 in the code AND in all 916 HAR
    entries. The original account.md attributed auth to Clerk entirely.
  * The session cookie is `user_token`, not `session_token` / `__session`.
  * Session TTL is UNKNOWN. The claimed "30 days" has no source.
  * Login is POST /api/v1/auth/email/login.

A failed login here returns a normalized error instead of `except: pass`
(the reference implementation at 01.06:519 swallows failures silently, which
makes a bad credential look like an unrelated downstream failure).
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .. import errors as err
from ..config import NoteGPTConfig
from . import request as request_mod


def login(config: NoteGPTConfig, scraper: Any = None) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Authenticate with email + password and return (token, error).

    Exactly one of the two is non-None.
    Credentials come from the environment via NoteGPTConfig — never arguments,
    so they cannot end up in a traceback or a log line.
    """
    if not config.email or not config.password:
        return None, err.ProviderError(
            category=err.INVALID_CREDENTIAL,
            retryable=False,
            provider_code="missing_credentials",
            safe_message="NOTEGPT_EMAIL / NOTEGPT_PASSWORD are not configured.",
        ).to_dict()

    scraper = scraper or request_mod.create_scraper()

    # T-10 — the login endpoint was the ONLY request in the package sent
    # WITHOUT the IP-rotation headers, so it alone attracted app code 164010
    # (rate limit). Verified before this change:
    #     build_headers() : accept, accept-encoding, accept-language,
    #                       client-ip, content-type, origin, referer,
    #                       user-agent, x-forwarded-for, x-real-ip
    #     login()         : accept, content-type, origin, referer, user-agent
    #     missing         : client-ip, x-forwarded-for, x-real-ip (+2 accept-*)
    #
    # Reuse `build_headers()` rather than re-deriving the trio locally: there is
    # then a single definition of the rotation header set, so the two paths
    # cannot drift apart again. Login-specific values are layered on top:
    # `referer` points at /login, and the charset-qualified Content-Type of the
    # auth endpoint is preserved exactly as it was.
    # Keys must match `build_headers()`' casing exactly. Adding "Accept" next to
    # its existing "accept" would send BOTH variants (requests does not fold
    # case in a plain dict) — caught by the duplicate-key test below.
    headers = request_mod.build_headers(config)
    headers.pop("Authorization", None)   # never send a stale token to /login
    headers["content-type"] = "application/json; charset=UTF-8"
    headers["referer"] = f"{config.origin}/login"
    payload = {"email": config.email, "password": config.password}

    try:
        response = scraper.post(
            config.url("login"),
            json=payload,
            headers=headers,
            timeout=10,
        )
    except Exception as exc:
        return None, err.normalize_error(exc).to_dict()

    # Auth failures arrive as HTTP 200 with an app code — check the body.
    try:
        body = response.json()
    except Exception:
        return None, err.normalize_error(
            http_status=response.status_code,
            body=None,
        ).to_dict()

    if not err.is_success_code(body.get("code")):
        return None, err.normalize_error(
            http_status=response.status_code,
            body=body,
        ).to_dict()

    data = body.get("data", {}) or {}
    token = data.get("access_token") or data.get("token")
    if not token:
        return None, err.ProviderError(
            category=err.INVALID_CREDENTIAL,
            retryable=False,
            provider_code="no_token_in_response",
            safe_message="Login succeeded but no token was returned.",
        ).to_dict()

    config.set_session_token(token)
    return token, None


def refresh_session(config: NoteGPTConfig, scraper: Any = None) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Re-authenticate after code 164003 ("login expired").

    NoteGPT exposes no refresh-token endpoint, so refresh == full re-login.
    """
    return login(config, scraper=scraper)


def build_auth_context(
    config: NoteGPTConfig,
    *,
    session_token: Optional[str] = None,
    anon_user_id: Optional[str] = None,
    sbox_guid: Optional[str] = None,
) -> Dict[str, Any]:
    """Assemble the headers + cookies pair for an authenticated request."""
    token = session_token or config.session_token
    return {
        "headers": request_mod.build_headers(config, session_token=token),
        "cookies": request_mod.build_cookies(
            session_token=token,
            anon_user_id=anon_user_id,
            sbox_guid=sbox_guid,
        ),
    }


# ==============================================================================
# NOT SUPPORTED
# ==============================================================================
# 31 §12 — mark unsupported modules as not-applicable, not as pending TODOs.

def oauth_flow(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """NOT_APPLICABLE — NoteGPT uses email/password + session cookie, not OAuth.

    account.md mentioned "Google OAuth" for web sign-up, but no OAuth endpoint
    appears in any HAR entry, and the code never performs an OAuth exchange.
    """
    return err.unsupported_capability("oauth_flow").to_dict()


def validate_api_key(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """NOT_SUPPORTED — no public API-key interface is known.

    CORRECTIONS.md §1 marks this UNKNOWN rather than unsupported: absence of
    evidence is not evidence of absence (§13). Should an API-key surface be
    discovered later, implement it here.
    """
    return err.unsupported_capability("api_key_validation").to_dict()


def csrf_token(*args: Any, **kwargs: Any) -> Optional[str]:
    """UNKNOWN — no CSRF token observed on POST /api/v2/chat/* calls."""
    return None
