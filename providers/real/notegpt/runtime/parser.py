# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Runtime — SSE Stream Parser
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §9 (response parsing)
         01_30 §15.3 (provider agent event normalization)
SOURCE : inventory/notegpt/CORRECTIONS_ROUND2.md §2 — the authoritative
         13-event list · projects/ngpt/scripts/01.06 :700-735, :783-800

WHY THIS FILE MATTERS
---------------------
ROUND2 §2 found that every original inventory file, AND the first corrections
pass, MISSED the `text` event — the event that carries the actual response
content. Any rebuild based on those documents would stream nothing.

The complete verified set (13 events + 1 alias), confirmed by
`grep -oE 'etype == "[a-z_]+"' 01.06` :

    text · reasoning · sandbox · sandbox_ready · tool_call · tool_call_result
    tool_result(alias) · credit_usage · continue_needed · agent_tool_limit
    length · error · info · done

Also note: the original generation.md claimed events `thought`, `credit`,
`tool_result` and a `data: [DONE]` terminator. Of those only `tool_result`
exists — and only as an alias. `thought` does not exist at all.
================================================================================
"""

from __future__ import annotations

import json
from typing import Any, Dict, Generator, Iterable, Optional

from .. import errors as err

SSE_PREFIX = "data: "
DONE_SENTINEL = "[DONE]"

# --- Content-bearing events -------------------------------------------------
EVENT_TEXT = "text"                    # the actual answer content
EVENT_REASONING = "reasoning"          # think/reasoning trace
EVENT_SANDBOX = "sandbox"
EVENT_SANDBOX_READY = "sandbox_ready"
EVENT_TOOL_CALL = "tool_call"
EVENT_TOOL_CALL_RESULT = "tool_call_result"
EVENT_TOOL_RESULT_ALIAS = "tool_result"   # alias — code checks BOTH spellings
EVENT_CREDIT_USAGE = "credit_usage"
EVENT_CONTINUE_NEEDED = "continue_needed"
EVENT_AGENT_TOOL_LIMIT = "agent_tool_limit"
EVENT_LENGTH = "length"
EVENT_ERROR = "error"
EVENT_INFO = "info"
EVENT_DONE = "done"

KNOWN_EVENTS = frozenset({
    EVENT_TEXT, EVENT_REASONING, EVENT_SANDBOX, EVENT_SANDBOX_READY,
    EVENT_TOOL_CALL, EVENT_TOOL_CALL_RESULT, EVENT_TOOL_RESULT_ALIAS,
    EVENT_CREDIT_USAGE, EVENT_CONTINUE_NEEDED, EVENT_AGENT_TOOL_LIMIT,
    EVENT_LENGTH, EVENT_ERROR, EVENT_INFO, EVENT_DONE,
})

# App codes that trigger identity rotation — 01.06:798
ROTATION_CODES = frozenset({164019, 164002, 164003})

# --- 30 §15.3 platform event names -----------------------------------------
PLATFORM_EVENT_MAP: Dict[str, str] = {
    EVENT_SANDBOX: "provider_agent.started",
    EVENT_SANDBOX_READY: "provider_agent.step_started",
    EVENT_TOOL_CALL: "provider_agent.tool_requested",
    EVENT_TOOL_CALL_RESULT: "provider_agent.tool_completed",
    EVENT_TOOL_RESULT_ALIAS: "provider_agent.tool_completed",
    EVENT_TEXT: "provider_agent.message_delta",
    EVENT_REASONING: "provider_agent.message_delta",
    EVENT_DONE: "provider_agent.completed",
    EVENT_ERROR: "provider_agent.failed",
}


def parse_sse_line(line: bytes | str) -> Optional[Dict[str, Any]]:
    """
    Parse one SSE line into a raw provider event dict.

    Returns None for keep-alives and non-data lines.
    Returns {"type": "done"} for the `[DONE]` sentinel.
    """
    if isinstance(line, bytes):
        decoded = line.decode("utf-8", errors="replace").strip()
    else:
        decoded = line.strip()

    if not decoded or not decoded.startswith(SSE_PREFIX):
        return None

    data_str = decoded[len(SSE_PREFIX):].strip()
    if data_str == DONE_SENTINEL:
        return {"type": EVENT_DONE, "content": DONE_SENTINEL}

    try:
        return json.loads(data_str)
    except json.JSONDecodeError:
        # 01.06:733 swallows these silently; we surface them as a typed event
        # so a malformed stream is observable instead of invisible.
        return {"type": EVENT_ERROR, "content": "malformed_sse_json", "raw_len": len(data_str)}


def iter_events(lines: Iterable[bytes | str]) -> Generator[Dict[str, Any], None, None]:
    """
    Normalize a raw SSE line iterator into typed provider events.

    Mirrors the dispatch logic of 01.06:700-735:
      - `reasoning` and `text` are read from FIELDS of the event object, not
        only from its `type` — an event may carry both at once.
      - a `done` event whose `reason` is `agent_tool_limit` or `length` is
        re-emitted as `continue_needed` (that is how auto-continue triggers).
    """
    for line in lines:
        event = parse_sse_line(line)
        if event is None:
            continue

        code = event.get("code")
        if code is not None and code in ROTATION_CODES:
            yield {
                "type": EVENT_INFO,
                "subtype": "identity_rotation_required",
                "code": code,
                "normalized_error": err.normalize_error(body={"code": code}).to_dict(),
            }
            continue

        etype = event.get("type")

        # Field-level content — an event can carry reasoning AND text.
        reasoning = event.get("reasoning")
        if reasoning:
            yield {"type": EVENT_REASONING, "content": reasoning}

        text = event.get("text")
        if text:
            yield {"type": EVENT_TEXT, "content": text}

        if etype == EVENT_DONE or event.get("done"):
            reason = event.get("reason", "")
            if reason in {EVENT_AGENT_TOOL_LIMIT, EVENT_LENGTH}:
                yield {"type": EVENT_CONTINUE_NEEDED, "reason": reason}
            else:
                yield {"type": EVENT_DONE, "content": DONE_SENTINEL}
            continue

        if etype == EVENT_CREDIT_USAGE:
            yield {"type": EVENT_CREDIT_USAGE, "credits": event.get("credit_usage") or event.get("content")}
            continue

        if etype in {EVENT_TOOL_CALL, EVENT_TOOL_CALL_RESULT, EVENT_TOOL_RESULT_ALIAS}:
            yield {
                "type": EVENT_TOOL_CALL if etype == EVENT_TOOL_CALL else EVENT_TOOL_CALL_RESULT,
                "tool": event.get("name") or event.get("tool"),
                "payload": event.get("args") or event.get("output") or event.get("content"),
            }
            continue

        if etype in KNOWN_EVENTS and etype not in {EVENT_TEXT, EVENT_REASONING}:
            yield {"type": etype, "content": event.get("content")}


def to_platform_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    30 §15.3 — map a provider event to a platform agent event.

    "The platform must not expose raw provider agent semantics directly to the
    rest of the Core."
    """
    etype = event.get("type")
    platform_name = PLATFORM_EVENT_MAP.get(etype)
    if not platform_name:
        return None
    return {
        "event": platform_name,
        "provider": "notegpt",
        "provider_event_type": etype,
        "data": {k: v for k, v in event.items() if k != "type"},
    }
