# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Tests — Asynchronous Sandbox Boot (T-09) & Login IP Rotation (T-10)
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §9, §15.3
SOURCE : live-runtime observation reported by Agent AG (postmortem §2).
         This is FIELD evidence, not 01.06 script evidence — tagged distinctly
         because it cannot be re-derived from the reference script.

WHY THIS FILE EXISTS
--------------------
The Daytona container boots ASYNCHRONOUSLY. The generation POST returns after
merely *scheduling* it, and for ~5-7s `agent-stream/continue` yields only
warm-up frames. Two independent defects made that unusable:

  T-09  The warm-up type names (`start`, `prepare_env`, `prepare_env_done`)
        were absent from KNOWN_EVENTS, and `iter_events()` ends with a
        `if etype in KNOWN_EVENTS` filter. Measured before the fix:
        4 warm-up lines in -> 0 events out. The run therefore ended with no
        content and no error — indistinguishable from an empty answer.

  T-10  `auth.login()` hand-rolled its header dict and was the ONLY request in
        the package sent WITHOUT the IP-rotation trio, so it alone attracted
        app code 164010 (rate limit).

REGRESSION GUARD ON THE FIX ITSELF
----------------------------------
The boot wait is bounded SEPARATELY from AUTO_CONTINUE_LIMIT. Tests here assert
that boot polling does NOT consume `sess.continue_calls`, because spending the
evidenced ceiling of 5 (01.06:104) on container warm-up would abort healthy
runs — which is exactly what raising the limit to 20 would have hidden.
================================================================================
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from providers.real.notegpt.config import AUTO_CONTINUE_LIMIT, NoteGPTConfig  # noqa: E402
from providers.real.notegpt.operations import provider_agent as agent_mod     # noqa: E402
from providers.real.notegpt.runtime import auth as auth_mod                   # noqa: E402
from providers.real.notegpt.runtime import parser as parser_mod               # noqa: E402

from . import mock_transport as mt                                            # noqa: E402


# ==============================================================================
# T-09a — the parser must not silently swallow warm-up frames
# ==============================================================================

BOOT_WIRE_LINES = [
    mt.line_boot(step=None, etype="start"),
    mt.line_boot(step="resume_sandbox"),
    mt.line_boot(step="resume_sandbox_done"),
    mt.line_boot(step=None, etype="prepare_env_done"),
]


def test_boot_frames_are_not_dropped_by_the_parser():
    """
    Regression: 4 warm-up lines used to yield 0 events.

    A dropped boot frame is the root cause of the whole failure mode — the
    caller cannot wait for something it never hears about.
    """
    events = list(parser_mod.iter_events(BOOT_WIRE_LINES))
    assert len(events) == len(BOOT_WIRE_LINES), (
        f"expected one event per warm-up line, got {len(events)}: {events}"
    )
    assert all(e["type"] == parser_mod.EVENT_SANDBOX for e in events)
    assert all(e.get("boot_pending") is True for e in events)


def test_boot_frames_reuse_the_known_sandbox_event_name():
    """
    Boot frames must surface under an ALREADY-KNOWN event type.

    Inventing a new public event name would force every downstream consumer
    (including the 30 §15.3 platform map) to learn it.
    """
    events = list(parser_mod.iter_events(BOOT_WIRE_LINES))
    for e in events:
        assert e["type"] in parser_mod.KNOWN_EVENTS
        assert e["type"] in parser_mod.PLATFORM_EVENT_MAP


def test_boot_frames_preserve_the_step_label():
    """The `step` field is the only progress signal a user can be shown."""
    events = list(parser_mod.iter_events(BOOT_WIRE_LINES))
    steps = [e.get("step") for e in events]
    assert steps == ["start", "resume_sandbox", "resume_sandbox_done", "prepare_env_done"]


def test_boot_frames_do_not_masquerade_as_continue_needed():
    """
    CRITICAL. `continue_needed` drives the T-01 truncation budget.

    If a boot frame were mapped to it, container warm-up would spend the
    evidenced ceiling of 5 and a healthy run would be cut off mid-answer.
    """
    events = list(parser_mod.iter_events(BOOT_WIRE_LINES))
    assert not [e for e in events if e["type"] == parser_mod.EVENT_CONTINUE_NEEDED]


def test_boot_frames_are_not_mistaken_for_content_or_done():
    """A booting container has produced neither an answer nor a completion."""
    events = list(parser_mod.iter_events(BOOT_WIRE_LINES))
    for forbidden in (parser_mod.EVENT_TEXT, parser_mod.EVENT_REASONING, parser_mod.EVENT_DONE):
        assert not [e for e in events if e["type"] == forbidden], (
            f"warm-up frame leaked as {forbidden}"
        )


# ==============================================================================
# T-09b — the agent must poll through the boot window
# ==============================================================================

@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    """Boot polling sleeps 1s per attempt; keep the suite fast."""
    monkeypatch.setattr(agent_mod, "CONTINUE_BACKOFF_SECONDS", 0)


def _run(transport, config=None):
    config = config or NoteGPTConfig()
    return list(agent_mod.stream_agent_run(config, {"prompt": "hi", "scraper": transport}))


def test_answer_is_recovered_after_an_async_boot():
    """
    End-to-end: generation yields ONLY warm-up frames, the answer arrives on a
    later continue poll. Before T-09 this run produced no text at all.
    """
    transport = mt.MockTransport(
        stream_script=[[mt.line_boot(step=None, etype="start")]],
        continue_script=[
            [mt.line_boot(step="resume_sandbox")],
            [mt.line_boot(step="resume_sandbox_done")],
            [mt.line_text("72"), mt.line_done()],
        ],
    )
    events = _run(transport)
    texts = [e.get("content") for e in events if e.get("type") == parser_mod.EVENT_TEXT]
    assert texts == ["72"], f"answer not recovered through boot window: {events}"
    assert transport.continue_requests >= 3


def test_boot_polling_does_not_consume_the_truncation_budget():
    """
    T-01 INVARIANT. Boot polls must not increment `sess.continue_calls`.

    Otherwise a 7s boot exhausts AUTO_CONTINUE_LIMIT=5 before the first token
    and the answer is truncated for a reason the user never caused.
    """
    from providers.real.notegpt.runtime import session as session_mod

    sess = session_mod.new_session()
    transport = mt.MockTransport(
        stream_script=[[mt.line_boot(step=None, etype="start")]],
        continue_script=[
            [mt.line_boot(step="resume_sandbox")],
            [mt.line_boot(step="resume_sandbox_done")],
            [mt.line_boot(step="resume_sandbox_done")],
            [mt.line_text("ok"), mt.line_done()],
        ],
    )
    list(agent_mod.stream_agent_run(
        NoteGPTConfig(), {"prompt": "hi", "scraper": transport, "session": sess}
    ))
    assert sess.continue_calls == 0, (
        f"boot polling burned {sess.continue_calls} of the "
        f"{AUTO_CONTINUE_LIMIT}-request truncation budget"
    )


def test_boot_wait_is_bounded_and_reports_a_retryable_error():
    """A permanently dead sandbox must terminate, not hang."""
    transport = mt.MockTransport(
        stream_script=[[mt.line_boot(step=None, etype="start")]],
        continue_script=[[mt.line_boot(step="resume_sandbox")]],   # never ready
        max_continue_requests=agent_mod.BOOT_POLL_LIMIT + 5,
    )
    events = _run(transport)
    errors = [e for e in events if e.get("type") == parser_mod.EVENT_ERROR]
    assert errors, "unbounded boot wait: no timeout error emitted"
    normalized = errors[-1]["normalized_error"]
    assert normalized["provider_code"] == "sandbox_boot_timeout"
    assert normalized["retryable"] is True
    assert transport.continue_requests <= agent_mod.BOOT_POLL_LIMIT


def test_boot_bound_is_independent_of_the_truncation_ceiling():
    """
    The two waits answer different questions and must not be unified.

    Pinning this keeps someone from "simplifying" by raising
    AUTO_CONTINUE_LIMIT — the shortcut that silently repeals 01.06:104.
    """
    assert agent_mod.BOOT_POLL_LIMIT != AUTO_CONTINUE_LIMIT
    assert agent_mod.BOOT_POLL_LIMIT > 7, "must cover the observed 5-7s boot"


def test_healthy_stream_never_enters_the_boot_wait():
    """No extra latency or requests when the container is already warm."""
    transport = mt.MockTransport(
        stream_script=[[mt.line_text("instant"), mt.line_done()]],
    )
    events = _run(transport)
    assert transport.continue_requests == 0
    assert [e.get("content") for e in events if e.get("type") == parser_mod.EVENT_TEXT] == ["instant"]


def test_boot_wait_exits_immediately_on_a_silent_stream():
    """
    A stream with neither boot frames nor content must not spin to the bound —
    there is nothing to wait for.
    """
    transport = mt.MockTransport(
        stream_script=[[mt.line_boot(step=None, etype="start")]],
        continue_script=[[]],           # silence
        max_continue_requests=agent_mod.BOOT_POLL_LIMIT + 5,
    )
    _run(transport)
    assert transport.continue_requests == 1, (
        f"spun {transport.continue_requests} times on a silent stream"
    )


def test_real_truncation_after_boot_still_uses_the_ceiling():
    """
    Boot recovery must not disable auto-continue: a genuine `continue_needed`
    arriving after the container warms up still goes through the T-01 path.
    """
    from providers.real.notegpt.runtime import session as session_mod

    sess = session_mod.new_session()
    transport = mt.MockTransport(
        stream_script=[[mt.line_boot(step=None, etype="start")]],
        continue_script=[
            [mt.line_boot(step="resume_sandbox")],
            [mt.line_text("part1"), mt.line_continue_needed("length")],
            [mt.line_text("part2"), mt.line_done()],
        ],
    )
    list(agent_mod.stream_agent_run(
        NoteGPTConfig(), {"prompt": "hi", "scraper": transport, "session": sess}
    ))
    assert sess.continue_calls >= 1, "real truncation was not counted"
    assert sess.continue_calls <= AUTO_CONTINUE_LIMIT


# ==============================================================================
# T-10 — login must carry the IP-rotation headers
# ==============================================================================

class _HeaderCapturingScraper:
    """
    Records the headers `auth.login()` actually passes to `scraper.post()`.

    Returns a benign auth-failure body so `login()` exits on its normal error
    path without a network call. We assert on the REQUEST, not the response.
    """

    def __init__(self) -> None:
        self.headers: dict = {}
        self.cookies: dict = {}

    def post(self, url: str, **kwargs):
        self.headers = dict(kwargs.get("headers") or {})

        class _Resp:
            status_code = 200

            @staticmethod
            def json():
                return {"code": 164001, "message": "invalid credentials"}

        return _Resp()


def _login_headers(config: NoteGPTConfig) -> dict:
    """
    Drive the REAL `auth.login()` and return the headers it actually sent.

    NOTE — why this is not a local re-implementation:
    the first version of these tests rebuilt the header dict here and asserted
    on the copy. Mutation testing exposed it as worthless: reverting
    `auth.login()` to its hand-rolled headers killed ZERO tests, because the
    replica had no connection to the code under test. Always go through the
    production function.
    """
    if not config.email:
        config._email = "probe@example.invalid"      # noqa: SLF001 — test probe
        config._password = "probe-password"          # noqa: SLF001
    scraper = _HeaderCapturingScraper()
    auth_mod.login(config, scraper=scraper)
    assert scraper.headers, "login() did not issue a request"
    return scraper.headers


def test_login_headers_carry_the_ip_rotation_trio():
    """
    Regression: login() previously sent only
    {accept, content-type, origin, referer, user-agent} — missing
    {client-ip, x-forwarded-for, x-real-ip}, hence the 164010 rate limit.
    """
    headers = _login_headers(NoteGPTConfig())
    for key in ("X-Forwarded-For", "X-Real-IP", "Client-IP"):
        assert key in headers, f"{key} missing from the login request"


def test_login_ip_headers_share_one_value():
    """01.06:552-566 sends the same IP in all three — reproduced verbatim."""
    headers = _login_headers(NoteGPTConfig())
    assert len({headers["X-Forwarded-For"], headers["X-Real-IP"], headers["Client-IP"]}) == 1


def test_login_headers_have_no_case_variant_duplicates():
    """
    Guards a bug introduced while writing this fix: adding "Accept" beside the
    existing "accept" makes `requests` send BOTH variants, a fingerprint no
    real browser produces.
    """
    headers = _login_headers(NoteGPTConfig())
    lowered = [k.lower() for k in headers]
    dupes = sorted({k for k in lowered if lowered.count(k) > 1})
    assert not dupes, f"case-variant duplicate headers: {dupes}"


def test_login_never_sends_a_stale_authorization_header():
    """Re-authentication must not present the token it is trying to replace."""
    config = NoteGPTConfig()
    config.set_session_token("stale-token-value")
    headers = _login_headers(config)
    assert "Authorization" not in headers
    assert "stale-token-value" not in " ".join(headers.values())


def test_login_preserves_its_endpoint_specific_values():
    """The charset-qualified content-type and /login referer are retained."""
    config = NoteGPTConfig()
    headers = _login_headers(config)
    assert headers["content-type"] == "application/json; charset=UTF-8"
    assert headers["referer"].endswith("/login")
