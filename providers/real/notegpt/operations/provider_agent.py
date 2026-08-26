# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Operation — Provider-Native Agent (Daytona Sandbox)
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §5, §15
SOURCE : projects/ngpt/scripts/01.06 :739-911 (ask_agent_stream)
                                     :694-736 (_send_continue_stream)
         inventory/notegpt/CORRECTIONS.md §10 · CORRECTIONS_ROUND2.md §2

DECLARED: capabilities.provider_agent = CONFIRMED (01.05:745-911)

30 §15 BOUNDARY
---------------
"Provider Agent Capability != Platform Agent Runtime"

This module runs the provider's agent and normalizes its events. It does NOT
own authorization, tool approval, tenant isolation, usage accounting, or the
final response — those stay with the platform (§15.4, §15.5).

STATE MODEL
-----------
There is no thread/run API. `conversation_id` IS the state handle, and keeping
it alive keeps the same sandbox (packages, files) across turns — notes.md
lesson #137. Consequently get/cancel-run are unsupported (see provider.py).
================================================================================
"""

from __future__ import annotations

import time
from typing import Any, Dict, Generator, List, Optional

from .. import errors as err
from ..config import NoteGPTConfig
from ..discovery import limits as limits_mod
from ..runtime import auth as auth_mod
from ..runtime import errors as runtime_errors
from ..runtime import parser as parser_mod
from ..runtime import request as request_mod
from ..runtime import session as session_mod


def _open_stream(
    config: NoteGPTConfig,
    scraper: Any,
    url: str,
    payload: Dict[str, Any],
    ctx: Dict[str, Any],
):
    """POST a streaming request. Returns (response, normalized_error)."""
    try:
        if hasattr(scraper, "cookies") and ctx.get("cookies"):
            scraper.cookies.update(ctx["cookies"])
        response = scraper.post(
            url,
            json=payload,
            headers=ctx["headers"],
            cookies=ctx["cookies"],
            stream=True,
            timeout=config.timeout,
        )
    except Exception as exc:
        return None, err.normalize_error(exc).to_dict()

    if getattr(response, "status_code", None) != 200:
        return None, err.normalize_error(http_status=response.status_code).to_dict()
    return response, None


def stream_agent_run(
    config: NoteGPTConfig,
    request: Dict[str, Any],
) -> Generator[Dict[str, Any], None, None]:
    """
    Run the agent and yield normalized events.

    Recovery behavior mirrors 01.06:
      * app codes 164019/164002/164003 -> rotate identity, retry SAME
        conversation_id (keeps the sandbox alive)
      * `continue_needed` -> call agent-stream/continue, bounded by
        AUTO_CONTINUE_LIMIT (01.06:104)
    """
    prompt = request.get("prompt") or request.get("message")
    if not prompt:
        yield {
            "type": parser_mod.EVENT_ERROR,
            "normalized_error": err.ProviderError(
                category=err.BAD_REQUEST,
                retryable=False,
                provider_code="missing_prompt",
                safe_message="A prompt/message is required.",
            ).to_dict(),
        }
        return

    sess: session_mod.ConversationSession = request.get("session") or session_mod.new_session(
        model=request.get("model"),
        is_auto_model=bool(request.get("is_auto_model", False)),
    )
    if request.get("conversation_id"):
        sess.conversation_id = request["conversation_id"]

    scraper = request.get("scraper") or request_mod.create_scraper()

    # Authenticate if credentials exist (01.06:495-521)
    if not config.session_token and config.email and config.password:
        try:
            _, login_error = auth_mod.login(config, scraper=scraper)
            if login_error:
                # If login is rate-limited (164010) or fails, continue with anonymous guest identity (01.06:519)
                pass
        except Exception:
            pass

    ctx = auth_mod.build_auth_context(
        config,
        anon_user_id=sess.anon_user_id,
        sbox_guid=sess.sbox_guid,
    )
    payload = request_mod.build_stream_payload(
        config,
        prompt,
        sess.conversation_id,
        model=sess.model,
        is_auto_model=sess.is_auto_model,
        files=request.get("files"),
    )

    yield {"type": parser_mod.EVENT_SANDBOX, "step": "initializing_sandbox"}

    # 01.06:741 — Pre-register chat session on NoteGPT /api/v2/ai-chat
    session_mod.create_chat_session(config, scraper, sess, prompt, ctx)

    response, open_error = _open_stream(config, scraper, config.url("chat_stream"), payload, ctx)
    if open_error:
        sess.error_encountered = open_error.get("category")
        yield {"type": parser_mod.EVENT_ERROR, "normalized_error": open_error}
        return

    rotated_once = False
    has_content = False

    for event in parser_mod.iter_events(response.iter_lines()):
        etype = event.get("type")

        # --- Identity rotation + retry (01.06:798-812) ----------------------
        if etype == parser_mod.EVENT_INFO and event.get("subtype") == "identity_rotation_required":
            sess.quota_exhausted = True
            yield event
            if rotated_once:
                yield {
                    "type": parser_mod.EVENT_ERROR,
                    "normalized_error": err.normalize_error(
                        body={"code": event.get("code")}
                    ).to_dict(),
                }
                return
            rotated_once = True
            sess.rotate_identity(keep_conversation=True)
            ctx = auth_mod.build_auth_context(
                config,
                anon_user_id=sess.anon_user_id,
                sbox_guid=sess.sbox_guid,
            )
            response, retry_error = _open_stream(
                config, scraper, config.url("chat_stream"), payload, ctx
            )
            if retry_error:
                yield {"type": parser_mod.EVENT_ERROR, "normalized_error": retry_error}
                return

            for sub_ev in parser_mod.iter_events(response.iter_lines()):
                sub_etype = sub_ev.get("type")
                if sub_etype == parser_mod.EVENT_TOOL_CALL:
                    sess.record_tool(sub_ev.get("tool"))
                elif sub_etype == parser_mod.EVENT_CREDIT_USAGE:
                    sess.record_credits(sub_ev.get("credits"))
                elif sub_etype in (parser_mod.EVENT_TEXT, parser_mod.EVENT_REASONING):
                    has_content = True
                yield sub_ev
            break

        if etype == parser_mod.EVENT_TOOL_CALL:
            sess.record_tool(event.get("tool"))
        elif etype == parser_mod.EVENT_CREDIT_USAGE:
            sess.record_credits(event.get("credits"))
        elif etype in (parser_mod.EVENT_TEXT, parser_mod.EVENT_REASONING):
            has_content = True

        if etype == parser_mod.EVENT_ERROR:
            normalized = runtime_errors.parse_stream_error(event)
            if normalized:
                event["normalized_error"] = normalized
                sess.error_encountered = normalized.get("category")
            yield event
            return

        yield event

        if etype == parser_mod.EVENT_DONE and has_content:
            break

    # 🔄 Auto-continue loop (01.06:890-908) to fetch reasoning and complete answer until [DONE]
    continue_attempts = 0
    done_received = False
    max_attempts = getattr(config, "max_continue_attempts", 25)
    while not done_received and continue_attempts < max_attempts:
        continue_attempts += 1
        sess.continue_calls = continue_attempts
        sess.recovery_used = True
        yield {
            "type": parser_mod.EVENT_INFO,
            "subtype": "auto_continue",
            "step": f"استئناف الساندبوكس #{continue_attempts}",
            "content": f"🔄 [استئناف تلقائي]: جاري تشغيل الساندبوكس واستلام الرد (استئناف #{continue_attempts})...",
        }
        time.sleep(1)
        for c_event in _continue_stream(config, scraper, sess, ctx):
            ce_type = c_event.get("type")
            if ce_type == parser_mod.EVENT_DONE:
                done_received = True
                yield c_event
                break
            elif ce_type == parser_mod.EVENT_CONTINUE_NEEDED:
                done_received = False
                break
            else:
                yield c_event


def _continue_stream(
    config: NoteGPTConfig,
    scraper: Any,
    sess: session_mod.ConversationSession,
    ctx: Dict[str, Any],
) -> Generator[Dict[str, Any], None, None]:
    """Resume a truncated run — POST /api/v2/chat/agent-stream/continue."""
    payload = request_mod.build_continue_payload(sess.conversation_id)
    response, open_error = _open_stream(
        config, scraper, config.url("agent_continue"), payload, ctx
    )
    if open_error:
        yield {"type": parser_mod.EVENT_ERROR, "normalized_error": open_error}
        return

    for event in parser_mod.iter_events(response.iter_lines()):
        if event.get("type") == parser_mod.EVENT_CONTINUE_NEEDED:
            if not limits_mod.should_auto_continue(sess.continue_calls):
                yield {
                    "type": parser_mod.EVENT_DONE,
                    "content": "[DONE]",
                    "finish_reason": "auto_continue_limit_reached",
                }
                return
            sess.continue_calls += 1
            yield from _continue_stream(config, scraper, sess, ctx)
            return
        yield event


def run_provider_agent(config: NoteGPTConfig, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Blocking agent run — accumulates the stream into one normalized result.
    """
    text_parts: List[str] = []
    reasoning_parts: List[str] = []
    tools: List[str] = []
    credits = 0
    finish_reason: Optional[str] = None
    error: Optional[Dict[str, Any]] = None

    sess = request.get("session") or session_mod.new_session(
        model=request.get("model"),
        is_auto_model=bool(request.get("is_auto_model", False)),
    )
    forwarded = dict(request)
    forwarded["session"] = sess

    for event in stream_agent_run(config, forwarded):
        etype = event.get("type")
        if etype == parser_mod.EVENT_TEXT:
            text_parts.append(str(event.get("content") or ""))
        elif etype == parser_mod.EVENT_REASONING:
            reasoning_parts.append(str(event.get("content") or ""))
        elif etype == parser_mod.EVENT_TOOL_CALL:
            tool = event.get("tool")
            if tool and tool not in tools:
                tools.append(tool)
        elif etype == parser_mod.EVENT_CREDIT_USAGE:
            try:
                credits += int(event.get("credits") or 0)
            except (TypeError, ValueError):
                pass
        elif etype == parser_mod.EVENT_ERROR:
            error = event.get("normalized_error") or err.normalize_error(
                stream_event="error"
            ).to_dict()
            break
        elif etype == parser_mod.EVENT_DONE:
            finish_reason = event.get("finish_reason") or "done"
            break

    if error:
        return {"error": error, "telemetry": sess.to_dict()}

    return {
        "result": {
            "text": "".join(text_parts),
            "reasoning": "".join(reasoning_parts),
            "conversation_id": sess.conversation_id,
            "tools_invoked": tools,
            "credits_used": credits,
            "finish_reason": finish_reason,
        },
        "telemetry": sess.to_dict(),
    }


def to_platform_events(events) -> Generator[Dict[str, Any], None, None]:
    """30 §15.3 — re-emit provider events as platform agent events."""
    for event in events:
        mapped = parser_mod.to_platform_event(event)
        if mapped:
            yield mapped
