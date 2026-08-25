# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Provider — Configuration (SSOT)
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §6.2
SOURCE : inventory/notegpt/CORRECTIONS.md §2 (endpoints verified vs code + HAR)

SECRETS POLICY
--------------
30 §2  : "Core must not store provider secrets directly."
30 §18.3: "no secret leakage in logs"
31 §19.5: "Implement credential handling without plaintext secrets."

Credentials are read from environment variables ONLY. There are no literal
credential values anywhere in this module. See projects/ngpt/.env.example.

Note: the legacy scripts under projects/ngpt/scripts/ hardcode staging
credentials (documented in CORRECTIONS_ROUND2.md §0). Those scripts are the
evidence source for this provider, not its runtime — this package does not
inherit that pattern.
================================================================================
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ==============================================================================
# Endpoints — CORRECTIONS.md §2
# ==============================================================================
BASE_URL = "https://notegpt.io"
AGENT_REFERER = "https://notegpt.io/ai-agent"
ORIGIN_URL = "https://notegpt.io"

ENDPOINTS: Dict[str, str] = {
    # Generation
    "chat_stream": "/api/v2/chat/stream",                    # 01.06:81 · HAR x62
    "agent_continue": "/api/v2/chat/agent-stream/continue",  # 01.06:82 · HAR x10
    "chat_record": "/api/v2/ai-chat",                        # x119/x4/x129

    # Auth
    "login": "/api/v1/auth/email/login",                     # 01.06:109

    # Health / quota
    "user_info": "/api/v1/userinfo",                         # HAR x10
    "plan_quota": "/api/v2/plan-quota",                      # HAR x212
    "quota_usage": "/api/v2/user/quota-usage",               # HAR x212
    "user_quota": "/api/v2/user/quota",                      # HAR x11

    # Agent discovery
    "agent_share_list": "/api/v1/agent/share/list",          # HAR x16

    # Assets (documented, NOT implemented — ROUND2 §3)
    "upload_sign_url": "/api/v1/upload/sign-url",

    # Misc
    "payment_permissions": "/api/v2/payments/check-user-permissions",  # HAR x6
}

# ==============================================================================
# Protocol constants
# ==============================================================================
SUCCESS_CODE = 100000        # CORRECTIONS.md §3 — HAR x728, NOT 0
DEFAULT_MODEL = "deepseek-v4-flash"   # 01.06:100
REQUEST_TIMEOUT = 120        # 01.06:103
AUTO_CONTINUE_LIMIT = 5      # 01.06:104
MAX_ATTACHED_SOURCES = 5     # 01.06:106
MAX_SAVED_PROJECTS = 10      # 01.06:105

# ROUND2 §2 — the complete SSE event set (13 + 1 alias).
# "text" was missing from every original inventory file; it carries the
# actual response content, so any rebuild without it would lose the answer.
SSE_EVENTS: List[str] = [
    "text",
    "reasoning",
    "sandbox",
    "sandbox_ready",
    "tool_call",
    "tool_call_result",
    "tool_result",        # alias — code compares against BOTH spellings
    "credit_usage",
    "continue_needed",
    "agent_tool_limit",
    "length",
    "error",
    "info",
    "done",
]

# Cookie names — CORRECTIONS.md §1
COOKIE_PRIMARY = "user_token"          # NOT "session_token"
COOKIE_ANON = "anonymous_user_id"
COOKIE_SBOX = "sbox-guid"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)

# Env var names (names only — never values)
ENV_EMAIL = "NOTEGPT_EMAIL"
ENV_PASSWORD = "NOTEGPT_PASSWORD"
ENV_SESSION_TOKEN = "NOTEGPT_SESSION_TOKEN"


@dataclass
class NoteGPTConfig:
    """Runtime configuration. Credentials come from the environment only."""

    base_url: str = BASE_URL
    referer: str = AGENT_REFERER
    origin: str = ORIGIN_URL
    model: str = DEFAULT_MODEL
    timeout: int = REQUEST_TIMEOUT
    auto_continue_limit: int = AUTO_CONTINUE_LIMIT
    max_attached_sources: int = MAX_ATTACHED_SOURCES
    user_agent: str = USER_AGENT
    endpoints: Dict[str, str] = field(default_factory=lambda: dict(ENDPOINTS))

    # Populated from env at construction; never logged.
    _email: Optional[str] = field(default=None, repr=False)
    _password: Optional[str] = field(default=None, repr=False)
    _session_token: Optional[str] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self._email = os.environ.get(ENV_EMAIL) or None
        self._password = os.environ.get(ENV_PASSWORD) or None
        self._session_token = os.environ.get(ENV_SESSION_TOKEN) or None

    # --- Credential accessors ------------------------------------------------
    @property
    def has_credentials(self) -> bool:
        return bool(self._email and self._password) or bool(self._session_token)

    @property
    def email(self) -> Optional[str]:
        return self._email

    @property
    def password(self) -> Optional[str]:
        return self._password

    @property
    def session_token(self) -> Optional[str]:
        return self._session_token

    def set_session_token(self, token: str) -> None:
        self._session_token = token

    def url(self, key: str) -> str:
        """Absolute URL for a named endpoint."""
        if key not in self.endpoints:
            raise KeyError(f"unknown endpoint: {key}")
        return f"{self.base_url}{self.endpoints[key]}"

    # --- Safety --------------------------------------------------------------
    def redacted(self) -> Dict[str, object]:
        """
        Log-safe view. 30 §18.3 "no secret leakage in logs".
        Never add credential values to this dict.
        """
        return {
            "base_url": self.base_url,
            "model": self.model,
            "timeout": self.timeout,
            "auto_continue_limit": self.auto_continue_limit,
            "has_email": bool(self._email),
            "has_password": bool(self._password),
            "has_session_token": bool(self._session_token),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"NoteGPTConfig({self.redacted()})"

    __str__ = __repr__
