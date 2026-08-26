# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT — Auto-Continue Loop Bound Tests (T-02)
================================================================================
SPEC : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §18.4

WHY THESE EXIST
---------------
`test_contract.py::test_auto_continue_limit_is_five` asserted only on the
helper `should_auto_continue()`. It passed while the real loop could send 25
requests, because no test ever executed the loop. These tests drive
`stream_agent_run()` end to end through MockTransport and assert on
BEHAVIOUR + COUNTER + FINISH REASON — not merely the absence of an exception.

Baseline for reference (measured against the pre-T-01 code):
    clean first stream        -> 5 continue requests were sent anyway
    stream never sends done   -> 25 continue requests (the phantom fallback)

Run: python3 -m pytest providers/real/notegpt/tests/test_auto_continue.py -v
================================================================================
"""

from __future__ import annotations

import pytest

from providers.real.notegpt.discovery import limits as limits_mod
from providers.real.notegpt.operations import provider_agent as pa
from providers.real.notegpt.runtime import parser as parser_mod

from . import mock_transport as mt


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Neutralize the inter-attempt backoff so tests stay fast."""
    monkeypatch.setattr(pa, "CONTINUE_BACKOFF_SECONDS", 0)


def _drive(config, session, transport):
    """Run the agent to completion and return the collected events."""
    return list(
        pa.stream_agent_run(
            config,
            {"prompt": "unit-test prompt", "scraper": transport, "session": session},
        )
    )


def _finish_reasons(events):
    return [e.get("finish_reason") for e in events if e.get("type") == parser_mod.EVENT_DONE]


# ==============================================================================
# The ceiling itself
# ==============================================================================
def test_limit_constant_is_five_and_single_sourced():
    """T-01: one origin for the value, re-exported — never two literals."""
    from providers.real.notegpt import config as config_mod

    assert limits_mod.AUTO_CONTINUE_LIMIT == 5
    assert config_mod.AUTO_CONTINUE_LIMIT == 5
    assert limits_mod.AUTO_CONTINUE_LIMIT is config_mod.AUTO_CONTINUE_LIMIT


def test_no_phantom_config_fallback_remains():
    """
    The old ceiling came from `getattr(config, "max_continue_attempts", 25)`,
    a key that never existed on the config object. Guard against its return.

    Comments are stripped first: the fix documents the removed defect by name,
    so a naive substring search would match the explanation, not live code.
    """
    import inspect

    code_lines = []
    for raw in inspect.getsource(pa.stream_agent_run).splitlines():
        stripped = raw.strip()
        if stripped.startswith("#"):
            continue
        code_lines.append(raw.split("  #")[0])
    code = "\n".join(code_lines)

    assert "max_continue_attempts" not in code, "phantom config key is back in live code"
    assert "getattr(config" not in code, "an unverified config fallback was reintroduced"
    # The ceiling must be referenced, never re-literalized.
    assert "should_auto_continue" in code


# ==============================================================================
# 1-3, 5 — the loop stops at the ceiling, counter is truthful, reason is set
# ==============================================================================
def test_loop_stops_exactly_at_limit(config, session, transport_factory):
    """Provider asks for continuation forever: exactly 5 requests, then stop."""
    transport = transport_factory(
        stream_script=[[mt.line_text("partial"), mt.line_continue_needed()]],
        continue_script=[[mt.line_continue_needed()]],
    )
    events = _drive(config, session, transport)

    assert transport.continue_requests == limits_mod.AUTO_CONTINUE_LIMIT == 5
    assert session.continue_calls == 5
    assert "auto_continue_limit_reached" in _finish_reasons(events)


def test_no_sixth_attempt_is_ever_sent(config, session, transport_factory):
    """Explicitly: there is no 6th request, and the counter does not reach 6."""
    transport = transport_factory(
        stream_script=[[mt.line_text("partial"), mt.line_continue_needed()]],
        continue_script=[[mt.line_continue_needed()]],
    )
    _drive(config, session, transport)

    assert transport.continue_requests <= 5, "a 6th continue request was sent"
    assert session.continue_calls <= 5, "counter exceeded the ceiling"


def test_counter_matches_requests_actually_sent(config, session, transport_factory):
    """
    `sess.continue_calls` must equal the number of continue POSTs — no
    double-counting between caller and callee.
    """
    transport = transport_factory(
        stream_script=[[mt.line_text("partial"), mt.line_continue_needed()]],
        continue_script=[
            [mt.line_continue_needed()],
            [mt.line_continue_needed()],
            [mt.line_text("rest"), mt.line_done()],
        ],
    )
    _drive(config, session, transport)

    assert session.continue_calls == transport.continue_requests == 3


# ==============================================================================
# 4, 6 — absence of continue_needed ends the loop immediately
# ==============================================================================
def test_clean_first_stream_sends_no_continue(config, session, transport_factory):
    """
    REGRESSION GUARD: the first stream ends with [DONE], so no continuation is
    required. Pre-fix this still fired 5 requests, burning quota on every call.
    """
    transport = transport_factory(
        stream_script=[[mt.line_text("complete answer"), mt.line_done()]],
        continue_script=[[mt.line_continue_needed()]],
    )
    _drive(config, session, transport)

    assert transport.continue_requests == 0, "continue was sent without being asked"
    assert session.continue_calls == 0


def test_counter_stays_zero_without_continue_needed(config, session, transport_factory):
    """Requirement 6: counter is 0 when no continuation was ever requested."""
    transport = transport_factory(
        stream_script=[[mt.line_reasoning("think"), mt.line_text("answer"), mt.line_done()]],
        continue_script=[[mt.line_continue_needed()]],
    )
    _drive(config, session, transport)

    assert session.continue_calls == 0
    assert transport.continue_requests == 0


# ==============================================================================
# 7 — natural end before the ceiling stops immediately
# ==============================================================================
def test_natural_end_before_limit_stops_early(config, session, transport_factory):
    """Two continuations then a real [DONE]: stop at 2, not 5."""
    transport = transport_factory(
        stream_script=[[mt.line_text("partial"), mt.line_continue_needed()]],
        continue_script=[
            [mt.line_continue_needed()],
            [mt.line_text("the rest"), mt.line_done()],
        ],
    )
    events = _drive(config, session, transport)

    assert transport.continue_requests == 2
    assert session.continue_calls == 2
    assert "auto_continue_limit_reached" not in _finish_reasons(events)


def test_exhausted_stream_does_not_loop(config, session, transport_factory):
    """
    A continue response that carries content but neither `done` nor
    `continue_needed` must not re-arm the loop (pre-fix: 25 requests).
    """
    transport = transport_factory(
        stream_script=[[mt.line_text("partial"), mt.line_continue_needed()]],
        continue_script=[[mt.line_text("trailing chunk")]],
    )
    _drive(config, session, transport)

    assert transport.continue_requests == 1
    assert session.continue_calls == 1


# ==============================================================================
# 8 — the 5th response is processed before the ceiling is enforced
# ==============================================================================
def test_fifth_response_is_processed_then_bounded(config, session, transport_factory):
    """
    The 5th attempt's payload must reach the consumer; only the 6th REQUEST is
    refused. Content must not be dropped at the boundary.
    """
    transport = transport_factory(
        stream_script=[[mt.line_text("partial"), mt.line_continue_needed()]],
        continue_script=[
            [mt.line_continue_needed()],
            [mt.line_continue_needed()],
            [mt.line_continue_needed()],
            [mt.line_continue_needed()],
            [mt.line_text("fifth-payload"), mt.line_continue_needed()],
        ],
    )
    events = _drive(config, session, transport)

    texts = [e.get("content") for e in events if e.get("type") == parser_mod.EVENT_TEXT]
    assert "fifth-payload" in texts, "the 5th response body was discarded"
    assert transport.continue_requests == 5
    assert session.continue_calls == 5
    assert "auto_continue_limit_reached" in _finish_reasons(events)


def test_blocking_runner_reports_limit_reason(config, transport_factory):
    """The blocking wrapper surfaces the bounded finish reason to callers."""
    transport = transport_factory(
        stream_script=[[mt.line_text("partial"), mt.line_continue_needed()]],
        continue_script=[[mt.line_continue_needed()]],
    )
    out = pa.run_provider_agent(
        config, {"prompt": "p", "scraper": transport, "session": None}
    )

    assert out["result"]["finish_reason"] == "auto_continue_limit_reached"
    assert out["telemetry"]["continue_calls"] == 5


# ==============================================================================
# Telemetry honesty
# ==============================================================================
def test_recovery_flag_only_set_when_continue_used(config, session, transport_factory):
    """`recovery_used` must not be asserted when nothing was recovered."""
    transport = transport_factory(
        stream_script=[[mt.line_text("done in one"), mt.line_done()]],
    )
    _drive(config, session, transport)

    assert session.recovery_used is False
    assert session.to_dict()["continue_calls"] == 0
