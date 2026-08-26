# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Tests — Mock Transport Layer (T-05)
================================================================================
SPEC : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §18.4
       01_31_PROVIDER_SCAFFOLDING_AND_ONBOARDING.md §11

WHY THIS EXISTS
---------------
The contract suite could not exercise the streaming control flow at all: every
test asserted on static data, so the auto-continue loop was never executed by
any test. That is precisely how a runaway ceiling survived review.

This module simulates the `scraper` object that `operations/provider_agent.py`
consumes, at the *same* interface the production code already uses:

    scraper.cookies                      -> a dict that gets .update()d
    scraper.post(url, json=..., headers=..., cookies=..., stream=..., timeout=...)
        -> object exposing .status_code and .iter_lines()

No network. No third-party host. No real credentials. The mock emits raw SSE
*wire lines* (``data: {...}``) and lets `runtime/parser.py` do the real
normalization, so tests exercise the genuine parse path rather than a
simplified shape that would pass while production fails.

PLACEMENT RULE
--------------
This file lives under `tests/` only and is never imported by the provider
package: test scaffolding is not part of the product (Core isolation).
================================================================================
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional

# --- SSE wire-line builders -------------------------------------------------
# These mirror the real payload shapes consumed by runtime/parser.iter_events.

DONE_SENTINEL_LINE = b"data: [DONE]"


def sse(obj: Dict[str, Any]) -> bytes:
    """Encode one provider event as a raw SSE wire line."""
    return b"data: " + json.dumps(obj, ensure_ascii=False).encode("utf-8")


def line_text(content: str = "hello") -> bytes:
    """A content-bearing event (parser reads the `text` FIELD, not the type)."""
    return sse({"text": content})


def line_reasoning(content: str = "thinking") -> bytes:
    return sse({"reasoning": content})


def line_done() -> bytes:
    """Natural end of stream."""
    return DONE_SENTINEL_LINE


def line_continue_needed(reason: str = "length") -> bytes:
    """
    A `done` event whose reason is `length` / `agent_tool_limit`.

    runtime/parser.py re-emits this as EVENT_CONTINUE_NEEDED — that is the only
    way auto-continue is triggered in production.
    """
    return sse({"type": "done", "reason": reason})


def line_tool_call(name: str = "python3") -> bytes:
    return sse({"type": "tool_call", "name": name, "args": {}})


def line_credit_usage(credits: int = 1) -> bytes:
    return sse({"type": "credit_usage", "credit_usage": credits})


def line_rotation(code: int = 164019) -> bytes:
    """Quota/identity code — parser turns it into identity_rotation_required."""
    return sse({"code": code})


class MockResponse:
    """Minimal stand-in for a streaming `requests` response."""

    def __init__(self, lines: Iterable[bytes], status_code: int = 200) -> None:
        self._lines: List[bytes] = list(lines)
        self.status_code = status_code

    def iter_lines(self):
        for line in self._lines:
            yield line


class MockTransport:
    """
    Scriptable stand-in for the `scraper` used by provider_agent.

    Construction
    ------------
    stream_script    : list of SSE line-lists. One entry per POST to
                       `chat_stream`. The last entry repeats if exhausted.
    continue_script  : list of SSE line-lists, one per POST to
                       `agent_continue`. The last entry repeats if exhausted,
                       which is what makes an unbounded loop observable.

    Recorded state (assert on these)
    --------------------------------
    stream_requests   : count of generation POSTs
    continue_requests : count of continue POSTs  <-- the quota-burn metric
    session_payloads  : bodies POSTed to `chat_record` (session pre-registration)
    urls              : every URL in call order

    Safety
    ------
    `max_continue_requests` hard-stops a runaway loop so a defective
    implementation fails the assertion instead of hanging the suite.
    """

    def __init__(
        self,
        stream_script: Optional[List[List[bytes]]] = None,
        continue_script: Optional[List[List[bytes]]] = None,
        status_code: int = 200,
        max_continue_requests: int = 60,
    ) -> None:
        self.cookies: Dict[str, Any] = {}
        self.stream_script = stream_script if stream_script is not None else [[line_text(), line_done()]]
        self.continue_script = continue_script if continue_script is not None else [[line_done()]]
        self.status_code = status_code
        self.max_continue_requests = max_continue_requests

        self.stream_requests = 0
        self.continue_requests = 0
        self.session_payloads: List[Dict[str, Any]] = []
        self.urls: List[str] = []

    # -- helpers ------------------------------------------------------------
    @staticmethod
    def _pick(script: List[List[bytes]], index: int) -> List[bytes]:
        """Return entry `index`, repeating the final entry once exhausted."""
        if not script:
            return []
        if index < len(script):
            return script[index]
        return script[-1]

    # -- the interface production code actually calls ------------------------
    def post(self, url: str, **kwargs: Any) -> MockResponse:
        self.urls.append(url)

        if "agent-stream/continue" in url:
            lines = self._pick(self.continue_script, self.continue_requests)
            self.continue_requests += 1
            if self.continue_requests > self.max_continue_requests:
                raise AssertionError(
                    f"Runaway auto-continue: exceeded {self.max_continue_requests} "
                    "continue requests. The loop is not bounded."
                )
            return MockResponse(lines, self.status_code)

        if "ai-chat" in url:
            # Session pre-registration (T-03 observation point).
            payload = kwargs.get("json")
            if isinstance(payload, dict):
                self.session_payloads.append(payload)
            return MockResponse([], 200)

        lines = self._pick(self.stream_script, self.stream_requests)
        self.stream_requests += 1
        return MockResponse(lines, self.status_code)

    # -- convenience readers -------------------------------------------------
    def first_chat_item(self) -> Dict[str, Any]:
        """The single chat_list entry sent during session pre-registration."""
        assert self.session_payloads, "no session pre-registration POST was made"
        return self.session_payloads[0]["content"]["chat_list"][0]
