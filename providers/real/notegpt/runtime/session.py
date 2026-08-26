# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Runtime — Conversation / Sandbox Session State
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §9
SOURCE : projects/ngpt/scripts/01.06 :356-384 · :596-692
         inventory/notegpt/notes.md §3 (lesson #137, CONFIRMED by CORRECTIONS.md §9)

THE KEY BEHAVIOR
----------------
`conversation_id` IS the provider-managed agent state. Preserving it keeps the
same Daytona sandbox alive across turns, so installed packages and files
persist. Rotating identity (IP/cookies) while keeping conversation_id is the
whole reason the reference implementation survives quota errors mid-session.

This module keeps that state in memory. The reference implementation persists
it to `active_session.txt`, which is script-local convenience, not provider
protocol — the platform owns its own persistence (tenant-scoped, 30 §15.4).
================================================================================
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_LOG = logging.getLogger(__name__)


@dataclass
class ConversationSession:
    """Provider-managed agent state for one NoteGPT conversation."""

    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    anon_user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sbox_guid: str = field(default_factory=lambda: str(uuid.uuid4()))
    model: Optional[str] = None
    is_auto_model: bool = False
    created_at: float = field(default_factory=time.time)

    # Telemetry — mirrors 01.06:483-493
    turns: int = 1
    continue_calls: int = 0
    credits_used: int = 0
    quota_exhausted: bool = False
    ip_rotated: bool = False
    recovery_used: bool = False
    tools_invoked: List[str] = field(default_factory=list)
    error_encountered: Optional[str] = None

    def new_conversation(self) -> str:
        """Start a fresh conversation — discards the sandbox session."""
        self.conversation_id = str(uuid.uuid4())
        self.turns = 1
        self.continue_calls = 0
        self.credits_used = 0
        self.tools_invoked = []
        self.error_encountered = None
        return self.conversation_id

    def rotate_identity(self, keep_conversation: bool = True) -> None:
        """
        Rotate IP/cookie identity. With keep_conversation=True (the default and
        the only safe choice mid-task) the sandbox session survives.

        NOTE: this is identity rotation only — NOT account rotation.
        CORRECTIONS.md §7: no account pool exists.
        """
        self.anon_user_id = str(uuid.uuid4())
        self.sbox_guid = str(uuid.uuid4())
        self.ip_rotated = True
        self.recovery_used = True
        if not keep_conversation:
            self.new_conversation()

    def record_tool(self, tool_name: Optional[str]) -> None:
        if tool_name and tool_name not in self.tools_invoked:
            self.tools_invoked.append(tool_name)

    def record_credits(self, credits: Any) -> None:
        try:
            self.credits_used += int(credits)
        except (TypeError, ValueError):
            pass

    def to_dict(self) -> Dict[str, Any]:
        """Log-safe snapshot — contains no credentials."""
        return {
            "conversation_id": self.conversation_id,
            "model": self.model,
            "is_auto_model": self.is_auto_model,
            "turns": self.turns,
            "continue_calls": self.continue_calls,
            "credits_used": self.credits_used,
            "quota_exhausted": self.quota_exhausted,
            "ip_rotated": self.ip_rotated,
            "recovery_used": self.recovery_used,
            "tools_invoked": list(self.tools_invoked),
            "error_encountered": self.error_encountered,
            "age_seconds": round(time.time() - self.created_at, 2),
        }


def new_session(model: Optional[str] = None, is_auto_model: bool = False) -> ConversationSession:
    return ConversationSession(model=model, is_auto_model=is_auto_model)


def resume_session(
    conversation_id: str,
    model: Optional[str] = None,
    is_auto_model: bool = False,
) -> ConversationSession:
    """
    Resume an existing conversation, keeping its sandbox alive (lesson #137).
    """
    session = ConversationSession(model=model, is_auto_model=is_auto_model)
    session.conversation_id = conversation_id
    return session


def create_chat_session(
    config: Any,
    scraper: Any,
    sess: ConversationSession,
    prompt: str,
    ctx: Dict[str, Any],
    sources: Optional[List[Any]] = None,
) -> None:
    """
    Pre-register chat session on NoteGPT /api/v2/ai-chat (01.06:596-629).

    T-03 — `sources` are the caller's attachments. They are converted to the
    browser-history `fileInfos[]` shape (7 fields, 01.06:580-594) by the module
    that owns that schema. `fileInfos` was previously hardcoded to `[]`, so
    attachments never appeared in the provider's own history record even when
    they were sent with the generation request.

    Failure here is non-fatal by design: pre-registration only populates the
    provider's "Recents" list, so a failure must not abort a usable run.
    """
    file_infos: List[Dict[str, Any]] = []
    if sources:
        # Imported lazily: this is the only runtime -> assets dependency, and a
        # module-level import would create a cycle via assets -> config.
        from ..assets import upload as upload_mod

        file_infos = upload_mod.build_history_file_infos(sources)

    try:
        now_ms = int(time.time() * 1000)
        payload = {
            "source": "agent",
            "content": {
                "title": prompt[:40],
                "updateTime": now_ms,
                "chat_list": [{
                    "label": prompt,
                    "question": prompt,
                    "answer": [""],
                    "reasoning": [{"startedAt": None, "endedAt": None, "reasoning": "", "thinkingSeconds": 0}],
                    "blocks": [],
                    "isStreaming": True,
                    "isInterrupted": False,
                    "generatedFiles": [],
                    "conversation_id": sess.conversation_id,
                    "created_at": now_ms,
                    "fileInfo": None,
                    "fileInfos": file_infos,
                    "modelValue": sess.model or config.model,
                    "isAutoModel": sess.is_auto_model,
                    "isStopped": False,
                }],
            },
        }
        scraper.post(config.url("chat_record"), json=payload, headers=ctx["headers"], cookies=ctx["cookies"], timeout=5)
    except Exception as exc:
        # T-07 — previously `except Exception: pass`, which made every failure
        # invisible: a broken pre-registration looked identical to a successful
        # one. The control flow is unchanged (still non-fatal), but the failure
        # is now diagnosable.
        #
        # Logged: exception TYPE, endpoint KEY, and attachment COUNT only.
        # Never the payload, prompt, headers, cookies or any token — the body
        # carries user content and the context carries credentials.
        _LOG.warning(
            "chat session pre-registration failed: %s (endpoint=%s, attachments=%d) "
            "— run continues; provider history may be incomplete",
            type(exc).__name__,
            "chat_record",
            len(file_infos),
        )
