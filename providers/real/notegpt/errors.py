# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Provider — Error Normalization
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §14
SOURCE : inventory/notegpt/CORRECTIONS.md §3, §8 · CORRECTIONS_ROUND2.md §6

The single most important fact encoded in this module
-----------------------------------------------------
NoteGPT returns application errors with **HTTP 200**:

    HTTP/1.1 200 OK
    {"code": 164003, "message": "login expired"}

Therefore the HTTP status line MUST NOT be used alone to detect failure.
`normalize_error()` always inspects the JSON `code` field first.

Success code is 100000 (HAR x728). `code: 0` NEVER appears in 916 HAR
entries — the value claimed by the original inventory/notegpt/health.md.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional

# ==============================================================================
# Normalized categories — 30 §14 (exact list, do not extend without versioning)
# ==============================================================================
AUTH_EXPIRED = "auth_expired"
INVALID_CREDENTIAL = "invalid_credential"
RATE_LIMITED = "rate_limited"
QUOTA_EXCEEDED = "quota_exceeded"
MODEL_UNAVAILABLE = "model_unavailable"
PROVIDER_UNAVAILABLE = "provider_unavailable"
UNSUPPORTED_CAPABILITY = "unsupported_capability"
BAD_REQUEST = "bad_request"
CONTENT_REJECTED = "content_rejected"
TIMEOUT = "timeout"
RETRYABLE_SERVER_ERROR = "retryable_server_error"
NON_RETRYABLE_ERROR = "non_retryable_error"

ALL_CATEGORIES = frozenset({
    AUTH_EXPIRED, INVALID_CREDENTIAL, RATE_LIMITED, QUOTA_EXCEEDED,
    MODEL_UNAVAILABLE, PROVIDER_UNAVAILABLE, UNSUPPORTED_CAPABILITY,
    BAD_REQUEST, CONTENT_REJECTED, TIMEOUT, RETRYABLE_SERVER_ERROR,
    NON_RETRYABLE_ERROR,
})

# Provider success sentinel — CORRECTIONS.md §3 (HAR x728)
SUCCESS_CODE = 100000


@dataclass
class ProviderError:
    """Normalized error envelope — 30 §14 required shape."""
    category: str
    retryable: bool
    provider_code: str
    safe_message: str
    retry_after_ms: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.category not in ALL_CATEGORIES:
            raise ValueError(f"unknown normalized category: {self.category}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ==============================================================================
# Application code map — CORRECTIONS.md §3 (verified against 916 HAR entries)
# ==============================================================================
# Only codes with real evidence are mapped. Unmapped codes fall through to a
# conservative non_retryable_error rather than being guessed at.
APP_CODE_MAP: Dict[int, Dict[str, Any]] = {
    # HAR x14 · handled at 01.06:798 -> rotate_identity(keep_conversation=True)
    164019: {
        "category": QUOTA_EXCEEDED,
        "retryable": True,
        "safe_message": "Provider plan quota exhausted.",
        "recovery": "rotate_identity",
    },
    # HAR x8 · body says literally "login expired" — arrives with HTTP 200
    164003: {
        "category": AUTH_EXPIRED,
        "retryable": True,
        "safe_message": "Provider session expired; re-authentication required.",
        "recovery": "reauthenticate",
    },
    # Handled in code at 01.06:798 but 0 occurrences in HAR
    164002: {
        "category": INVALID_CREDENTIAL,
        "retryable": True,
        "safe_message": "Provider authentication failed.",
        "recovery": "reauthenticate",
    },
}

# ==============================================================================
# HTTP status map — used ONLY as a fallback when no app code is present.
# ==============================================================================
# CORRECTIONS.md §3: the full histogram of 916 entries is 200x837 · 304x11 · 0x68.
# 401 / 403 / 429 / 504 have ZERO occurrences. They are mapped defensively
# because they are plausible for a Cloudflare-fronted service, but each is
# tagged evidence="none" so no one mistakes them for observed behavior.
HTTP_STATUS_MAP: Dict[int, Dict[str, Any]] = {
    400: {"category": BAD_REQUEST, "retryable": False, "evidence": "none"},
    401: {"category": AUTH_EXPIRED, "retryable": True, "evidence": "none"},
    403: {"category": PROVIDER_UNAVAILABLE, "retryable": True, "evidence": "none"},
    404: {"category": BAD_REQUEST, "retryable": False, "evidence": "none"},
    408: {"category": TIMEOUT, "retryable": True, "evidence": "none"},
    429: {"category": RATE_LIMITED, "retryable": True, "evidence": "none"},
    500: {"category": RETRYABLE_SERVER_ERROR, "retryable": True, "evidence": "none"},
    502: {"category": RETRYABLE_SERVER_ERROR, "retryable": True, "evidence": "none"},
    503: {"category": PROVIDER_UNAVAILABLE, "retryable": True, "evidence": "none"},
    504: {"category": TIMEOUT, "retryable": True, "evidence": "none"},
}

# SSE stream events that carry failure semantics — ROUND2 §2 (13 events total)
STREAM_ERROR_EVENTS: Dict[str, Dict[str, Any]] = {
    "error": {
        "category": NON_RETRYABLE_ERROR,
        "retryable": False,
        "safe_message": "Provider stream reported an error.",
    },
    "agent_tool_limit": {
        "category": QUOTA_EXCEEDED,
        "retryable": False,
        "safe_message": "Provider agent tool-call ceiling reached.",
    },
    "length": {
        "category": QUOTA_EXCEEDED,
        "retryable": True,
        "safe_message": "Provider response truncated at length limit.",
        "recovery": "auto_continue",
    },
}


def is_success_code(code: Any) -> bool:
    """True only for the provider's real success sentinel (100000)."""
    try:
        return int(code) == SUCCESS_CODE
    except (TypeError, ValueError):
        return False


def normalize_error(
    error: Any = None,
    *,
    http_status: Optional[int] = None,
    body: Optional[Dict[str, Any]] = None,
    stream_event: Optional[str] = None,
) -> ProviderError:
    """
    Normalize any NoteGPT failure into the 30 §14 envelope.

    Resolution order is deliberate:
      1. JSON app code   — authoritative, because errors arrive with HTTP 200
      2. SSE event type  — stream-level failures
      3. HTTP status     — fallback only
      4. Exception type  — transport-level failures
    """
    # --- 1. Application code (authoritative) --------------------------------
    if body and isinstance(body, dict) and "code" in body:
        raw_code = body.get("code")
        if not is_success_code(raw_code):
            try:
                code_int = int(raw_code)
            except (TypeError, ValueError):
                code_int = None

            if code_int in APP_CODE_MAP:
                spec = APP_CODE_MAP[code_int]
                return ProviderError(
                    category=spec["category"],
                    retryable=spec["retryable"],
                    provider_code=str(raw_code),
                    safe_message=spec["safe_message"],
                    details={
                        "recovery": spec.get("recovery"),
                        "http_status": http_status,
                        "source": "app_code",
                    },
                )
            # Unmapped app code — never guess a category.
            return ProviderError(
                category=NON_RETRYABLE_ERROR,
                retryable=False,
                provider_code=str(raw_code),
                safe_message="Provider returned an unrecognized error code.",
                details={
                    "http_status": http_status,
                    "source": "app_code_unmapped",
                    "evidence": "none",
                },
            )

    # --- 2. Stream event ----------------------------------------------------
    if stream_event and stream_event in STREAM_ERROR_EVENTS:
        spec = STREAM_ERROR_EVENTS[stream_event]
        return ProviderError(
            category=spec["category"],
            retryable=spec["retryable"],
            provider_code=f"sse:{stream_event}",
            safe_message=spec["safe_message"],
            details={"recovery": spec.get("recovery"), "source": "sse_event"},
        )

    # --- 3. HTTP status (fallback only) -------------------------------------
    if http_status is not None and http_status >= 400:
        spec = HTTP_STATUS_MAP.get(http_status)
        if spec:
            return ProviderError(
                category=spec["category"],
                retryable=spec["retryable"],
                provider_code=f"http:{http_status}",
                safe_message=f"Provider returned HTTP {http_status}.",
                details={"source": "http_status", "evidence": spec["evidence"]},
            )
        return ProviderError(
            category=NON_RETRYABLE_ERROR,
            retryable=False,
            provider_code=f"http:{http_status}",
            safe_message=f"Provider returned HTTP {http_status}.",
            details={"source": "http_status", "evidence": "none"},
        )

    # --- 4. Transport exception --------------------------------------------
    if error is not None:
        name = type(error).__name__
        if "Timeout" in name:
            return ProviderError(
                category=TIMEOUT,
                retryable=True,
                provider_code=name,
                safe_message="Provider request timed out.",
                details={"source": "exception"},
            )
        if "Connection" in name or "DNS" in name:
            return ProviderError(
                category=PROVIDER_UNAVAILABLE,
                retryable=True,
                provider_code=name,
                safe_message="Provider is unreachable.",
                details={"source": "exception"},
            )
        return ProviderError(
            category=NON_RETRYABLE_ERROR,
            retryable=False,
            provider_code=name,
            safe_message="Provider request failed.",
            details={"source": "exception"},
        )

    return ProviderError(
        category=NON_RETRYABLE_ERROR,
        retryable=False,
        provider_code="unknown",
        safe_message="Provider request failed for an unknown reason.",
        details={"source": "none"},
    )


def unsupported_capability(operation: str) -> ProviderError:
    """30 §8.1 — a provider without a declared capability must reject it."""
    return ProviderError(
        category=UNSUPPORTED_CAPABILITY,
        retryable=False,
        provider_code="unsupported_capability",
        safe_message=f"NoteGPT does not declare support for '{operation}'.",
        details={"operation": operation},
    )
