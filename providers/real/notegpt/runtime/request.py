# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Runtime — Request Mechanics
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §9
SOURCE : projects/ngpt/scripts/01.06_notegpt_agent_mode.py :549-566 (_build_headers)
         inventory/notegpt/notes.md §1-2 (verified by CORRECTIONS.md §9)

30 §9: "The Core must not see these details." Everything about headers,
cookies, TLS fingerprinting and IP rotation stays inside this module.
================================================================================
"""

from __future__ import annotations

import random
import uuid
from typing import Any, Dict, Optional

from ..assets import upload as upload_mod
from ..config import (
    COOKIE_ANON,
    COOKIE_NC,
    COOKIE_PRIMARY,
    COOKIE_SBOX,
    NoteGPTConfig,
)


def generate_fake_ip() -> str:
    """
    Random IPv4 for the X-Forwarded-For rotation.
    01.06:386 generate_fake_ip() · notes.md §2 (CONFIRMED by CORRECTIONS.md §9).
    """
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def build_headers(config: NoteGPTConfig, session_token: Optional[str] = None) -> Dict[str, str]:
    """
    Exact header set from 01.06:552-566.

    All three IP headers carry the SAME value in the reference implementation —
    reproduced verbatim rather than "improved", since this is the shape that is
    known to be accepted.
    """
    ip = generate_fake_ip()
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ar-EG,ar;q=0.9,en-US;q=0.8",
        "content-type": "application/json",
        "origin": config.origin,
        "referer": config.referer,
        "user-agent": config.user_agent,
        "X-Forwarded-For": ip,
        "X-Real-IP": ip,
        "Client-IP": ip,
    }
    token = session_token or config.session_token
    if token:
        # 01.06:564 — header alternative to the cookie (CORRECTIONS.md §1)
        headers["Authorization"] = f"Bearer {token}"
    return headers


def build_cookies(
    session_token: Optional[str] = None,
    anon_user_id: Optional[str] = None,
    sbox_guid: Optional[str] = None,
    nc_token: Optional[str] = None,
) -> Dict[str, str]:
    """
    Cookie jar shape from 01.06:476-481.

    CORRECTIONS.md §1: the primary cookie is `user_token`. The original
    inventory claimed `session_token` / `__session` — both are wrong.
    The reference login also carries `nc_token`, falling back to the fresh
    access token when the scraper did not set a separate value.
    """
    cookies = {
        COOKIE_ANON: anon_user_id or str(uuid.uuid4()),
        COOKIE_SBOX: sbox_guid or str(uuid.uuid4()),
    }
    if session_token:
        cookies[COOKIE_PRIMARY] = session_token
        cookies[COOKIE_NC] = nc_token or session_token
    return cookies


def create_scraper() -> Any:
    """
    curl_cffi / cloudscraper session for real Chrome TLS/JA3 fingerprints.
    Uses curl_cffi with chrome124 impersonation for stable HTTP/2 streaming.
    """
    try:
        from curl_cffi import requests as creq
        return creq.Session(impersonate="chrome124")
    except ImportError:
        import cloudscraper
        return cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "android", "desktop": False}
        )


def build_stream_payload(
    config: NoteGPTConfig,
    prompt: str,
    conversation_id: str,
    *,
    model: Optional[str] = None,
    is_auto_model: bool = False,
    files: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Generation payload — verbatim shape from 01.06:745-755.

    Note the field names: `chat_mode: "agent"` (not `agent_mode: true`) and
    `message` (not `prompt`). The original inventory/notegpt/generation.md
    documented a different, non-existent shape.

    ATTACHMENTS (T-03b root fix)
    ----------------------------
    `files` is NORMALIZED here rather than copied verbatim. Previously this
    builder trusted its caller, so whatever list it was handed went straight
    onto the wire. A caller passing raw attachment dicts therefore shipped
    ZERO of the 5 native fields plus a foreign `type` key whose 10/20 encoding
    belongs to the *history* `fileInfos[]` shape. Reproduced on this builder
    directly, before this change:
        keys sent   : ['name', 'size', 'type', 'url']       (0/5 native)
        keys wanted : ['file_content','file_name','file_size','file_url',
                       'mime_type']

    T-03b first fixed this at the single call site in `provider_agent.py`,
    because `runtime/request.py` was outside that round's approved scope. That
    left the builder still trusting its caller, so any NEW call site could
    reintroduce the exact same bug. The invariant now belongs to the function
    that owns the body: this builder cannot emit a malformed `files[]`
    regardless of who calls it.

    `build_stream_files_payload()` is idempotent (it reads BOTH the caller
    spelling `url`/`name`/`size` and the native `file_url`/`file_name`/
    `file_size`), verified once == twice == thrice, so the pre-existing call
    site that already normalizes stays correct and is not double-converted.
    """
    payload: Dict[str, Any] = {
        "message": prompt,
        "model": model or config.model,
        "language": "auto",
        "tone": "default",
        "length": "moderate",
        "chat_mode": "agent",
        "conversation_id": conversation_id,
        "isAutoModel": is_auto_model,
    }
    if files:
        # Native files array — 01.06:759-762
        normalized = upload_mod.build_stream_files_payload(files)
        if normalized:
            payload["files"] = normalized
    return payload


def build_continue_payload(conversation_id: str) -> Dict[str, Any]:
    """Resume payload — 01.06:697. Only the conversation id is sent."""
    return {"conversation_id": conversation_id}


def rotate_identity(
    config: NoteGPTConfig,
    *,
    keep_conversation: bool = True,
) -> Dict[str, Any]:
    """
    Identity rotation — 01.06:523-546.

    IMPORTANT (CORRECTIONS.md §7): this rotates IP + cookie identifiers on the
    SAME account. It is NOT account-pool rotation; accounts_notegpt.json does
    not exist. `keep_conversation=True` preserves conversation_id, which keeps
    the Daytona sandbox session alive (notes.md lesson #137).
    """
    return {
        "anon_user_id": str(uuid.uuid4()),
        "sbox_guid": str(uuid.uuid4()),
        "ip": generate_fake_ip(),
        "keep_conversation": keep_conversation,
        "rotation_type": "identity_only",   # never "account"
    }
