# -*- coding: utf-8 -*-
"""Regression tests for the 01.06 provider flow repairs.

The tests keep the SPEC-facing adapter and operation signatures unchanged while
checking the wire ordering and stream behavior that the reference implementation
and the supplied live-runtime report require.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from providers.real.notegpt.config import NoteGPTConfig
from providers.real.notegpt.operations import provider_agent as agent_mod
from providers.real.notegpt.runtime import auth as auth_mod
from providers.real.notegpt.runtime import parser as parser_mod
from providers.real.notegpt.runtime import request as request_mod
from providers.real.notegpt.runtime import session as session_mod

from . import mock_transport as mt


def _config_with_login_credentials() -> NoteGPTConfig:
    config = NoteGPTConfig()
    # Reserved test values only; never real credentials.
    config._email = "probe@example.test"  # noqa: SLF001 - test fixture
    config._password = "probe-password"  # noqa: SLF001 - test fixture
    return config


class _HeaderRecorder(mt.MockTransport):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.request_headers: List[Dict[str, str]] = []
        self.request_payloads: List[Dict[str, Any]] = []

    def post(self, url: str, **kwargs: Any) -> mt.MockResponse:
        self.request_headers.append(dict(kwargs.get("headers") or {}))
        self.request_payloads.append(dict(kwargs.get("json") or {}))
        return super().post(url, **kwargs)


def test_reference_boot_event_names_are_not_dropped():
    """The raw names used by 01.06 must enter the existing sandbox contract."""
    events = list(parser_mod.iter_events([
        mt.sse({"type": "create_sandbox", "data": {"message": "initializing_sandbox"}}),
        mt.sse({"type": "resume_sandbox", "data": {"message": "resume_sandbox"}}),
    ]))

    assert [event["type"] for event in events] == [
        parser_mod.EVENT_SANDBOX,
        parser_mod.EVENT_SANDBOX,
    ]
    assert [event["step"] for event in events] == [
        "initializing_sandbox",
        "resume_sandbox",
    ]
    assert all(event["boot_pending"] is True for event in events)


def test_non_rotation_app_code_is_surfaced_as_explicit_error():
    """`164001` must not disappear and become an unrelated empty-stream error."""
    events = list(parser_mod.iter_events([
        mt.sse({"code": 164001, "message": "wrong params"}),
    ]))
    assert len(events) == 1
    assert events[0]["type"] == parser_mod.EVENT_ERROR
    assert events[0]["normalized_error"]["provider_code"] == "164001"


def test_reference_boot_done_sentinel_still_polls_for_answer(monkeypatch):
    """A scheduling stream's `[DONE]` is not the final agent answer."""
    monkeypatch.setattr(agent_mod, "CONTINUE_BACKOFF_SECONDS", 0)
    transport = mt.MockTransport(
        stream_script=[[
            mt.sse({"type": "create_sandbox", "data": {"message": "initializing_sandbox"}}),
            mt.line_done(),
        ]],
        continue_script=[
            [mt.sse({"type": "resume_sandbox", "data": {"message": "resume_sandbox"}}), mt.line_done()],
            [mt.line_text("10"), mt.line_done()],
        ],
    )

    result = agent_mod.run_provider_agent(
        NoteGPTConfig(),
        {"prompt": "5+5", "scraper": transport, "session": session_mod.new_session()},
    )

    assert result["result"]["text"] == "10"
    assert transport.continue_requests == 2


def test_first_progress_event_follows_session_preregistration(monkeypatch):
    """01.06 registers `/api/v2/ai-chat` before exposing the stream status."""
    monkeypatch.setattr(agent_mod, "CONTINUE_BACKOFF_SECONDS", 0)
    transport = _HeaderRecorder(stream_script=[[mt.line_text("ok"), mt.line_done()]])
    events = agent_mod.stream_agent_run(
        NoteGPTConfig(),
        {"prompt": "p", "scraper": transport, "session": session_mod.new_session()},
    )

    first = next(events)
    assert first["type"] == parser_mod.EVENT_SANDBOX
    assert transport.urls == ["https://notegpt.io/api/v2/ai-chat"]
    list(events)
    assert transport.urls[1].endswith("/api/v2/chat/stream")


def test_continue_response_is_drained_after_continue_marker(monkeypatch):
    """A marker is not a reason to discard later text in the same response."""
    monkeypatch.setattr(agent_mod, "CONTINUE_BACKOFF_SECONDS", 0)
    transport = mt.MockTransport(
        stream_script=[[mt.line_text("part-1"), mt.line_continue_needed()]],
        continue_script=[[
            mt.line_continue_needed("length"),
            mt.line_text("tail-after-marker"),
            mt.line_done(),
        ]],
    )
    events = list(agent_mod.stream_agent_run(
        NoteGPTConfig(),
        {"prompt": "p", "scraper": transport, "session": session_mod.new_session()},
    ))

    texts = [e["content"] for e in events if e.get("type") == parser_mod.EVENT_TEXT]
    assert texts == ["part-1", "tail-after-marker"]
    assert any(e.get("type") == parser_mod.EVENT_DONE for e in events)
    assert transport.continue_requests == 1


def test_each_continue_request_gets_fresh_ip_headers(monkeypatch):
    """Continue calls reproduce the reference's per-request header rebuild."""
    monkeypatch.setattr(agent_mod, "CONTINUE_BACKOFF_SECONDS", 0)
    ips = iter(("10.0.0.1", "10.0.0.2", "10.0.0.3"))
    monkeypatch.setattr(request_mod, "generate_fake_ip", lambda: next(ips))
    transport = _HeaderRecorder(
        stream_script=[[mt.line_text("part"), mt.line_continue_needed()]],
        continue_script=[
            [mt.line_continue_needed()],
            [mt.line_text("done"), mt.line_done()],
        ],
    )

    list(agent_mod.stream_agent_run(
        NoteGPTConfig(),
        {"prompt": "p", "scraper": transport, "session": session_mod.new_session()},
    ))

    # Calls: initial context, then one fresh context per continue request.
    continue_headers = [
        h for url, h in zip(transport.urls, transport.request_headers)
        if "agent-stream/continue" in url
    ]
    assert [h["X-Forwarded-For"] for h in continue_headers] == [
        "10.0.0.2", "10.0.0.3"
    ]
    assert all(
        len({h["X-Forwarded-For"], h["X-Real-IP"], h["Client-IP"]}) == 1
        for h in continue_headers
    )


def test_recovery_refreshes_token_and_keeps_conversation(monkeypatch):
    """Recoverable app codes refresh auth but retry the same conversation."""
    monkeypatch.setattr(agent_mod, "CONTINUE_BACKOFF_SECONDS", 0)
    config = _config_with_login_credentials()
    # Model an already-authenticated run whose current session expires during
    # the stream; this skips the initial login and leaves refresh for recovery.
    config.set_session_token("old-token")
    refresh_calls = []

    def fake_refresh(current_config, scraper=None):
        refresh_calls.append(scraper)
        current_config.set_session_token("fresh-token")
        current_config.set_nc_token("fresh-nc-token")
        return "fresh-token", None

    monkeypatch.setattr(auth_mod, "refresh_session", fake_refresh)
    transport = _HeaderRecorder(
        stream_script=[
            [mt.line_rotation(164003)],
            [mt.line_text("recovered"), mt.line_done()],
        ],
    )
    sess = session_mod.new_session()
    conversation_id = sess.conversation_id

    events = list(agent_mod.stream_agent_run(
        config,
        {"prompt": "p", "scraper": transport, "session": sess},
    ))

    assert len(refresh_calls) == 1
    assert sess.conversation_id == conversation_id
    assert sess.ip_rotated is True
    assert [e["content"] for e in events if e.get("type") == parser_mod.EVENT_TEXT] == [
        "recovered"
    ]

    retry_headers = transport.request_headers[-1]
    retry_payload = transport.request_payloads[-1]
    assert retry_headers["Authorization"] == "Bearer fresh-token"
    assert retry_payload["conversation_id"] == conversation_id
    assert transport.request_headers[-1] is not transport.request_headers[-2]
    # The request context sent to the provider carries both observed cookies.
    # `_HeaderRecorder` records headers/payloads, so inspect the MockTransport
    # call through its cookie updates as the actual wire-side assertion.
    assert transport.cookies["user_token"] == "fresh-token"
    assert transport.cookies["nc_token"] == "fresh-nc-token"


def test_cli_hides_setup_messages_after_streaming_begins(monkeypatch, capsys):
    """The CLI phase gate prevents setup chatter from corrupting the answer."""
    from providers.real.notegpt import __main__ as cli

    class FakeConfig:
        email = ""
        has_credentials = False

    class FakeSession:
        conversation_id = "test-conversation"

    class FakeClient:
        def __init__(self, config=None, model=None, conversation_id=None):
            self.session = FakeSession()

        def stream(self, prompt):
            return iter([
                {"type": "sandbox", "step": "initial"},
                {"type": "info", "content": "initial-info"},
                {"type": "reasoning", "content": "thinking"},
                {"type": "info", "content": "late-info"},
                {"type": "sandbox", "step": "late-boot"},
                {"type": "text", "content": "answer"},
            ])

    monkeypatch.setattr(cli, "NoteGPTConfig", FakeConfig)
    monkeypatch.setattr(cli, "NoteGPTClient", FakeClient)
    monkeypatch.setattr(cli.sys, "argv", ["notegpt", "prompt", "--new"])

    session_file = Path(cli.__file__).resolve().parent / "active_session.txt"
    previous = session_file.read_bytes() if session_file.exists() else None
    try:
        if session_file.exists():
            session_file.unlink()
        cli.main()
    finally:
        if previous is None:
            session_file.unlink(missing_ok=True)
        else:
            session_file.write_bytes(previous)

    output = capsys.readouterr().out
    assert "initial" in output
    assert "initial-info" in output
    assert "thinking" in output
    assert "answer" in output
    assert "late-info" not in output
    assert "late-boot" not in output


def test_login_preserves_distinct_nc_token_cookie():
    """01.06 copies scraper `nc_token`, falling back only when absent."""
    config = _config_with_login_credentials()

    class LoginScraper:
        def __init__(self):
            self.cookies = {"nc_token": "server-nc-token"}

        def post(self, url: str, **kwargs: Any):
            class Response:
                status_code = 200

                @staticmethod
                def json():
                    return {"code": 100000, "data": {"access_token": "fresh-token"}}

            return Response()

    scraper = LoginScraper()
    token, error = auth_mod.login(config, scraper=scraper)

    assert token == "fresh-token"
    assert error is None
    assert config.nc_token == "server-nc-token"
    context = auth_mod.build_auth_context(config)
    assert context["cookies"]["user_token"] == "fresh-token"
    assert context["cookies"]["nc_token"] == "server-nc-token"
