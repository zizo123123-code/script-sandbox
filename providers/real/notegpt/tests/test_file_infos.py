# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT — Session Pre-Registration `fileInfos` Tests (T-03)
================================================================================
SPEC : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §18.4

WHY THESE EXIST
---------------
`create_chat_session()` hardcoded `"fileInfos": []`, so attachments never
reached the provider's own history record even when they were sent with the
generation request. The fix threads `sources` through the call chain:

    request["files"] -> stream_agent_run -> create_chat_session(sources=...)
                     -> upload.build_history_file_infos() -> fileInfos[]

Nothing asserted that chain, so the whole of T-03 could regress silently.
These tests drive `stream_agent_run()` through MockTransport and assert on the
BODY THAT WAS ACTUALLY POSTED to /api/v2/ai-chat.

THE TRAP THIS ALSO GUARDS
-------------------------
Two different attachment shapes exist and are easy to swap:
    history `fileInfos[]`  7 fields  {type, url_type, url, title, size,
                                      origin_url, transcriptUrl}
    stream  `files[]`      5 fields  {file_name, file_size, file_url,
                                      file_content, mime_type}
Sending one where the other belongs is silently ignored by the provider, so a
shape swap must fail here, loudly.

Run: python3 -m pytest providers/real/notegpt/tests/test_file_infos.py -v
================================================================================
"""

from __future__ import annotations

import pytest

from providers.real.notegpt.assets import upload as upload_mod
from providers.real.notegpt.operations import provider_agent as pa
from providers.real.notegpt.runtime import session as session_mod

from . import mock_transport as mt

# The 7 fields of the history shape — 01.06:580-594.
HISTORY_FIELDS = {
    "type", "url_type", "url", "title", "size", "origin_url", "transcriptUrl",
}
# The 5 fields of the generation shape — 01.06:273-296.
STREAM_FIELDS = {
    "file_name", "file_size", "file_url", "file_content", "mime_type",
}

IMAGE = {
    "url": "https://example.invalid/a.png",
    "name": "a.png",
    "type": "image",
    "size": 2048,
    "mime_type": "image/png",
}
DOC = {
    "url": "https://example.invalid/b.pdf",
    "name": "b.pdf",
    "type": "file",
    "size": 4096,
    "mime_type": "application/pdf",
}


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(pa, "CONTINUE_BACKOFF_SECONDS", 0)


def _run(config, transport, files=None):
    """Drive one clean agent run and return the pre-registration chat item."""
    request = {
        "prompt": "unit-test prompt",
        "scraper": transport,
        "session": session_mod.new_session(),
    }
    if files is not None:
        request["files"] = files
    list(pa.stream_agent_run(config, request))
    return transport.first_chat_item()


@pytest.fixture()
def clean_transport(transport_factory):
    """A transport whose first stream completes without continuation."""
    return transport_factory(
        stream_script=[[mt.line_text("ok"), mt.line_done()]],
    )


# ==============================================================================
# The call chain actually carries the attachments
# ==============================================================================
def test_attachments_reach_session_pre_registration(config, clean_transport):
    """
    THE regression guard: `fileInfos` was hardcoded `[]`. One attachment in,
    one attachment recorded in the history payload.
    """
    item = _run(config, clean_transport, files=[IMAGE])

    assert item["fileInfos"], "fileInfos is empty — attachments were dropped"
    assert len(item["fileInfos"]) == 1
    assert item["fileInfos"][0]["url"] == IMAGE["url"]
    assert item["fileInfos"][0]["title"] == "a.png"


def test_multiple_attachments_preserve_order(config, clean_transport):
    item = _run(config, clean_transport, files=[IMAGE, DOC])

    assert [f["title"] for f in item["fileInfos"]] == ["a.png", "b.pdf"]


def test_file_infos_uses_the_history_shape_exactly(config, clean_transport):
    """
    Seven fields, no more, no less — and NOT the generation `files[]` shape.
    A shape swap is the silent failure mode this test exists to catch.
    """
    item = _run(config, clean_transport, files=[DOC])
    entry = item["fileInfos"][0]

    assert set(entry) == HISTORY_FIELDS, f"wrong shape: {sorted(entry)}"
    assert not (set(entry) & STREAM_FIELDS), "generation shape leaked into history"


def test_image_and_document_get_distinct_type_codes(config, clean_transport):
    """01.06:580-594 — type 10 = image, 20 = document."""
    item = _run(config, clean_transport, files=[IMAGE, DOC])
    by_title = {f["title"]: f for f in item["fileInfos"]}

    assert by_title["a.png"]["type"] == 10
    assert by_title["b.pdf"]["type"] == 20


# ==============================================================================
# Compatibility — the no-attachment path must be untouched
# ==============================================================================
def test_no_attachments_still_sends_empty_list(config, clean_transport):
    """
    Backward compatibility: a run without files must keep the previous payload
    exactly — an empty list, never None and never a missing key.
    """
    item = _run(config, clean_transport)

    assert item["fileInfos"] == []
    assert item["fileInfo"] is None


def test_session_is_still_pre_registered_without_files(config, clean_transport):
    """The pre-registration POST itself must not become conditional."""
    _run(config, clean_transport)

    assert clean_transport.session_payloads, "pre-registration POST disappeared"
    assert any("ai-chat" in u for u in clean_transport.urls)


def test_empty_and_urlless_sources_are_ignored(config, transport_factory):
    """An attachment with no URL cannot be referenced — it must be skipped."""
    transport = transport_factory(stream_script=[[mt.line_text("ok"), mt.line_done()]])
    item = _run(config, transport, files=[{"name": "ghost.png", "type": "image"}])

    assert item["fileInfos"] == []


# ==============================================================================
# Pre-registration failure must never break a usable run (T-07 boundary)
# ==============================================================================
def test_pre_registration_failure_is_non_fatal_and_logged(config, caplog):
    """
    The history POST is best-effort. A failure must be logged (not swallowed)
    and must not abort the generation.
    """
    class FailingChatRecord(mt.MockTransport):
        def post(self, url, **kwargs):
            if "ai-chat" in url:
                raise RuntimeError("simulated pre-registration outage")
            return super().post(url, **kwargs)

    transport = FailingChatRecord(
        stream_script=[[mt.line_text("still works"), mt.line_done()]],
    )

    with caplog.at_level("WARNING"):
        events = list(pa.stream_agent_run(
            config,
            {
                "prompt": "p",
                "scraper": transport,
                "session": session_mod.new_session(),
                "files": [IMAGE],
            },
        ))

    texts = [e.get("content") for e in events if e.get("type") == "text"]
    assert "still works" in texts, "a history failure aborted a usable run"

    assert any("pre-registration failed" in r.message for r in caplog.records), (
        "the failure was swallowed silently — T-07 regression"
    )


def test_failure_log_leaks_no_payload_or_credentials(config, caplog):
    """The log line may carry the exception TYPE and a count — never content."""
    class FailingChatRecord(mt.MockTransport):
        def post(self, url, **kwargs):
            if "ai-chat" in url:
                raise RuntimeError("simulated outage")
            return super().post(url, **kwargs)

    secret_prompt = "SUPER-SECRET-PROMPT-TEXT"
    transport = FailingChatRecord(
        stream_script=[[mt.line_text("ok"), mt.line_done()]],
    )

    with caplog.at_level("WARNING"):
        list(pa.stream_agent_run(
            config,
            {
                "prompt": secret_prompt,
                "scraper": transport,
                "session": session_mod.new_session(),
                "files": [IMAGE],
            },
        ))

    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert secret_prompt not in logged, "the prompt was leaked into logs"
    assert IMAGE["url"] not in logged, "an attachment URL was leaked into logs"
    assert "RuntimeError" in logged, "the exception type should be diagnosable"


# ==============================================================================
# The two builders are genuinely different functions
# ==============================================================================
def test_the_two_payload_builders_do_not_agree():
    """
    If these ever return the same shape, one of them is wrong and the
    distinction that T-03 restored has collapsed.
    """
    history = upload_mod.build_history_file_infos([DOC])
    stream = upload_mod.build_stream_files_payload([DOC])

    assert set(history[0]) == HISTORY_FIELDS
    assert set(stream[0]) == STREAM_FIELDS
    assert history != stream


def test_deprecated_alias_still_returns_the_history_shape():
    """
    `build_native_files_payload()` is misleadingly named but callers may still
    use it; it must keep behaving as the history builder.
    """
    assert (
        upload_mod.build_native_files_payload([IMAGE])
        == upload_mod.build_history_file_infos([IMAGE])
    )


def test_builders_accept_native_field_spellings():
    """An attachment already in one native shape converts to the other."""
    native = {"file_url": "https://example.invalid/c.png", "file_name": "c.png",
              "file_size": 10, "type": "image"}
    entry = upload_mod.build_history_file_infos([native])[0]

    assert entry["url"] == native["file_url"]
    assert entry["title"] == "c.png"
    assert entry["size"] == 10
