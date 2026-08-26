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
from ..assets import upload as upload_mod
from ..config import NoteGPTConfig
from ..discovery import limits as limits_mod
from ..runtime import auth as auth_mod
from ..runtime import errors as runtime_errors
from ..runtime import parser as parser_mod
from ..runtime import request as request_mod
from ..runtime import session as session_mod

# Pause between auto-continue requests — mirrors the reference script's 1s wait
# (01.06:890-908). Named so tests can patch it instead of sleeping for real.
CONTINUE_BACKOFF_SECONDS = 1

# --- Asynchronous sandbox boot (T-09) ---------------------------------------
# SOURCE: live-runtime observation reported by Agent AG (postmortem §2), NOT
# 01.06. Field evidence, tagged distinctly from script-evidenced constants.
#
# The container boots asynchronously over ~5-7s, during which
# `agent-stream/continue` returns only warm-up frames (or nothing at all).
#
# This bound is SEPARATE from AUTO_CONTINUE_LIMIT on purpose. Those two waits
# answer different questions:
#
#   AUTO_CONTINUE_LIMIT = 5  -> "the answer was TRUNCATED, fetch the rest"
#                               (01.06:104, script-evidenced, must stay 5)
#   BOOT_POLL_LIMIT          -> "the container is not up YET, wait for it"
#                               (field-observed 5-7s)
#
# Sharing one budget would let a 7s boot spend the entire truncation ceiling
# before the first token, then abort a perfectly healthy run. The reference
# workaround of raising auto_continue_limit to 20 is exactly that mistake: it
# silently repeals the evidenced ceiling that T-01 was opened to restore.
#
# 12 * 1s = 12s, roughly 2x the observed worst case, so a slow boot survives
# while a permanently dead sandbox still terminates.
BOOT_POLL_LIMIT = 12


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
    # T-03 (payload confusion) — the two attachment shapes must not be crossed.
    # `request["files"]` holds caller-facing dicts ({url, name, type, size}).
    #   stream  files[]     -> build_stream_files_payload()  (file_name, ...)
    #   history fileInfos[] -> build_history_file_infos()    (type, url_type, ...)
    #
    # The normalization below is now REDUNDANT-BUT-HARMLESS: as of the T-03b
    # root fix, `build_stream_payload()` normalizes internally, so the invariant
    # no longer depends on this call site remembering to. It is kept because the
    # conversion is idempotent (once == twice) and because it keeps the intent
    # explicit at the point where caller attachments enter the generation path.
    sources = request.get("files")
    payload = request_mod.build_stream_payload(
        config,
        prompt,
        sess.conversation_id,
        model=sess.model,
        is_auto_model=sess.is_auto_model,
        files=upload_mod.build_stream_files_payload(sources) if sources else None,
    )

    yield {"type": parser_mod.EVENT_SANDBOX, "step": "initializing_sandbox"}

    # 01.06:741 — Pre-register chat session on NoteGPT /api/v2/ai-chat.
    # T-03: the caller's attachments must reach the history record too; passing
    # them lets session.py build the native `fileInfos[]` instead of sending [].
    session_mod.create_chat_session(
        config, scraper, sess, prompt, ctx, sources=request.get("files")
    )

    response, open_error = _open_stream(config, scraper, config.url("chat_stream"), payload, ctx)
    if open_error:
        sess.error_encountered = open_error.get("category")
        yield {"type": parser_mod.EVENT_ERROR, "normalized_error": open_error}
        return

    rotated_once = False
    has_content = False
    # T-01 — auto-continue is entered ONLY if the provider actually asked for it.
    continue_needed = False
    # T-09 — the generation POST only SCHEDULES the async container; warm-up
    # frames mean "not up yet", which is not the same as "finished".
    boot_pending = False
    stream_ended_naturally = False

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
                elif sub_etype == parser_mod.EVENT_CONTINUE_NEEDED:
                    continue_needed = True
                yield sub_ev
            break

        if etype == parser_mod.EVENT_TOOL_CALL:
            sess.record_tool(event.get("tool"))
        elif etype == parser_mod.EVENT_CREDIT_USAGE:
            sess.record_credits(event.get("credits"))
        elif etype in (parser_mod.EVENT_TEXT, parser_mod.EVENT_REASONING):
            has_content = True
        elif etype == parser_mod.EVENT_CONTINUE_NEEDED:
            continue_needed = True
        elif etype == parser_mod.EVENT_SANDBOX and event.get("boot_pending"):
            # T-09 — container still warming up. Recorded, but NOT translated
            # into `continue_needed`: that flag spends the T-01 truncation
            # budget, and boot waiting has its own bound.
            boot_pending = True

        if etype == parser_mod.EVENT_ERROR:
            normalized = runtime_errors.parse_stream_error(event)
            if normalized:
                event["normalized_error"] = normalized
                sess.error_encountered = normalized.get("category")
            yield event
            return

        yield event

        if etype == parser_mod.EVENT_DONE and has_content:
            stream_ended_naturally = True
            break

    # ── T-09: asynchronous sandbox boot wait ────────────────────────────────
    # Entered ONLY when the generation stream produced no content AND did not
    # end naturally — i.e. the container was still booting. Bounded by
    # BOOT_POLL_LIMIT, which is deliberately NOT the T-01 ceiling, and it does
    # NOT touch `sess.continue_calls`, so the truncation budget is untouched
    # and the T-01 tests keep asserting the same numbers.
    #
    # NOTE (contrast with the reference fix): the report's approach was to
    # remove the `break` on sandbox frames so one connection could be drained
    # to its tail. That conflates two things — draining a connection, and
    # re-polling after the container wakes. It also removes the guard that
    # stops a stream from being read past its natural end. Boot waiting is
    # handled here as its own explicitly-bounded phase instead.
    if not has_content and not stream_ended_naturally and boot_pending:
        boot_polls = 0
        while boot_polls < BOOT_POLL_LIMIT:
            boot_polls += 1
            time.sleep(CONTINUE_BACKOFF_SECONDS)
            saw_boot_frame = False
            for b_event in _continue_stream(config, scraper, sess, ctx):
                b_type = b_event.get("type")
                if b_type == parser_mod.EVENT_SANDBOX and b_event.get("boot_pending"):
                    saw_boot_frame = True
                    yield b_event
                    continue
                if b_type in (parser_mod.EVENT_TEXT, parser_mod.EVENT_REASONING):
                    has_content = True
                elif b_type == parser_mod.EVENT_CONTINUE_NEEDED:
                    continue_needed = True
                elif b_type == parser_mod.EVENT_TOOL_CALL:
                    sess.record_tool(b_event.get("tool"))
                elif b_type == parser_mod.EVENT_CREDIT_USAGE:
                    sess.record_credits(b_event.get("credits"))
                if b_type == parser_mod.EVENT_DONE:
                    yield b_event
                    return
                yield b_event
            # Content arrived, or the provider asked for a real continue:
            # the boot phase is over either way.
            if has_content or continue_needed:
                break
            if not saw_boot_frame:
                # Neither boot frame nor content. Nothing left to wait for;
                # do not spin silently to the bound.
                break
        else:
            # Bound exhausted while still only seeing warm-up frames.
            yield {
                "type": parser_mod.EVENT_ERROR,
                "normalized_error": err.ProviderError(
                    category=err.PROVIDER_UNAVAILABLE,
                    retryable=True,
                    provider_code="sandbox_boot_timeout",
                    safe_message=(
                        "Provider sandbox did not finish booting within "
                        f"{BOOT_POLL_LIMIT}s."
                    ),
                ).to_dict(),
            }
            return

    # 🔄 Auto-continue loop (01.06:890-908) to fetch reasoning and complete answer until [DONE]
    #
    # T-01 — the ceiling is `AUTO_CONTINUE_LIMIT` and nothing else. The previous
    # version read `getattr(config, "max_continue_attempts", 25)`, a key that
    # does not exist on NoteGPTConfig, so the fallback 25 always won over the
    # evidenced 5 (01.06:104). It also entered the loop unconditionally, firing
    # continue requests even when the first stream had already finished cleanly.
    #
    # `sess.continue_calls` is incremented in exactly ONE place below: once per
    # continue request actually sent. It does not move when `continue_needed` is
    # merely received, nor when a request is refused at the ceiling.
    while continue_needed:
        if not limits_mod.should_auto_continue(sess.continue_calls):
            # Ceiling reached: refuse the next request instead of sending it.
            yield {
                "type": parser_mod.EVENT_DONE,
                "content": "[DONE]",
                "finish_reason": "auto_continue_limit_reached",
            }
            return

        sess.continue_calls += 1          # <-- single increment site
        sess.recovery_used = True
        attempt = sess.continue_calls
        yield {
            "type": parser_mod.EVENT_INFO,
            "subtype": "auto_continue",
            "step": f"استئناف الساندبوكس #{attempt}",
            "content": f"🔄 [استئناف تلقائي]: جاري تشغيل الساندبوكس واستلام الرد (استئناف #{attempt})...",
        }
        time.sleep(CONTINUE_BACKOFF_SECONDS)

        # Re-evaluated per response: only a fresh `continue_needed` keeps the
        # loop alive. A natural end, an error, or an exhausted stream ends it.
        continue_needed = False
        for c_event in _continue_stream(config, scraper, sess, ctx):
            ce_type = c_event.get("type")
            if ce_type == parser_mod.EVENT_DONE:
                yield c_event
                return
            if ce_type == parser_mod.EVENT_CONTINUE_NEEDED:
                continue_needed = True
                break
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

    # T-01 — this function performs exactly ONE request and does not recurse.
    # It previously incremented `sess.continue_calls` and re-entered itself,
    # which meant the counter advanced in two different places (here and in the
    # caller's loop) and the ceiling was enforced on a value the caller had
    # already overwritten. Bounding and counting now live solely in the caller;
    # `continue_needed` is simply reported upward.
    for event in parser_mod.iter_events(response.iter_lines()):
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
