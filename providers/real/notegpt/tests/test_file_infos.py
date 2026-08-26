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
from providers.real.notegpt.runtime import request as request_mod
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


# ==============================================================================
# The GENERATION body must carry the stream shape (payload confusion)
# ==============================================================================
# The history side was wired and tested, but the generation side handed
# `request["files"]` straight to `build_stream_payload()`, which copies its
# argument verbatim. Result: the raw caller dicts went out on the wire with
# ZERO of the 5 native fields, plus a foreign `type` key whose 10/20 encoding
# belongs to the history shape. Reproduced before the fix:
#     keys sent   : ['name', 'size', 'type', 'url']
#     keys wanted : ['file_content','file_name','file_size','file_url','mime_type']
# These tests observe the body actually POSTed to the generation endpoint.
def test_generation_body_uses_the_stream_shape_exactly(config, clean_transport):
    """Five native fields, and none of the history fields."""
    _run(config, clean_transport, files=[IMAGE])
    body = clean_transport.first_stream_payload()

    assert "files" in body, "attachments never reached the generation body"
    entry = body["files"][0]
    assert set(entry) == STREAM_FIELDS, f"wrong shape: {sorted(entry)}"


def test_generation_body_does_not_leak_caller_or_history_keys(config, clean_transport):
    """
    The exact regression: raw caller keys must not survive into the body, and
    the history `type` code must never appear on the generation side.
    """
    _run(config, clean_transport, files=[IMAGE])
    entry = clean_transport.first_stream_payload()["files"][0]

    assert not (set(entry) & HISTORY_FIELDS), "history shape leaked into generation"
    for raw_key in ("url", "name", "size", "type"):
        assert raw_key not in entry, f"raw caller key {raw_key!r} leaked to the wire"


def test_generation_body_values_are_mapped_not_just_shaped(config, clean_transport):
    """A correct shape with wrong values would still be broken."""
    _run(config, clean_transport, files=[IMAGE])
    entry = clean_transport.first_stream_payload()["files"][0]

    assert entry["file_url"] == IMAGE["url"]
    assert entry["file_name"] == IMAGE["name"]
    assert entry["file_size"] == IMAGE["size"]
    assert entry["mime_type"] == IMAGE["mime_type"]


def test_both_sides_are_wired_from_one_source_in_one_run(config, clean_transport):
    """
    The two shapes are built from the SAME attachment in a single run: history
    gets fileInfos[], generation gets files[], neither borrows the other.
    """
    item = _run(config, clean_transport, files=[IMAGE, DOC])
    stream_files = clean_transport.first_stream_payload()["files"]

    assert len(item["fileInfos"]) == 2 and len(stream_files) == 2
    assert [f["title"] for f in item["fileInfos"]] == ["a.png", "b.pdf"]
    assert [f["file_name"] for f in stream_files] == ["a.png", "b.pdf"]
    assert set(item["fileInfos"][0]) == HISTORY_FIELDS
    assert set(stream_files[0]) == STREAM_FIELDS


def test_no_attachments_omits_files_key_entirely(config, clean_transport):
    """
    Compatibility: with no attachments the generation body must stay exactly as
    before (no empty `files` key introduced by the normalization).
    """
    _run(config, clean_transport)
    assert "files" not in clean_transport.first_stream_payload()


# ==============================================================================
# The BUILDER itself must own the invariant (T-03b root fix)
# ==============================================================================
# The tests above drive `stream_agent_run()`, so they only prove that ONE call
# site normalizes. `build_stream_payload()` still copied its `files` argument
# verbatim, which means the guarantee lived in the caller, not in the function
# that owns the body — any new call site could reintroduce the identical bug
# while every test above stayed green.
#
# Reproduced against the builder directly, before the root fix:
#     build_stream_payload(cfg, "hi", "c1", files=[{"url":..,"name":..,
#                                                  "type":..,"size":..}])
#     -> files[0] keys == ['name','size','type','url']   (0/5 native fields,
#                                                         foreign 'type' leaked)
#
# These tests call the builder with NO agent loop involved, so they fail if the
# normalization is ever moved back out of it.
def test_builder_normalizes_raw_caller_dicts_without_any_call_site(config):
    """The builder alone must emit the 5 native fields from raw caller dicts."""
    payload = request_mod.build_stream_payload(
        config, "hi", "conv-1", files=[IMAGE]
    )

    entry = payload["files"][0]
    assert set(entry) == STREAM_FIELDS, f"builder did not normalize: {sorted(entry)}"


def test_builder_rejects_history_shape_leaking_into_generation(config):
    """The history `type` code must not survive the builder."""
    entry = request_mod.build_stream_payload(
        config, "hi", "conv-1", files=[IMAGE]
    )["files"][0]

    assert not (set(entry) & HISTORY_FIELDS)
    for raw_key in ("url", "name", "size", "type"):
        assert raw_key not in entry, f"raw caller key {raw_key!r} survived the builder"


def test_builder_maps_values_not_only_shape(config):
    """A right-shaped body with wrong values is still a broken body."""
    entry = request_mod.build_stream_payload(
        config, "hi", "conv-1", files=[IMAGE]
    )["files"][0]

    assert entry["file_url"] == IMAGE["url"]
    assert entry["file_name"] == IMAGE["name"]
    assert entry["file_size"] == IMAGE["size"]
    assert entry["mime_type"] == IMAGE["mime_type"]


def test_builder_normalization_is_idempotent(config):
    """
    The pre-existing call site normalizes too, so the builder receives an
    ALREADY-native list. Converting twice must be a no-op, otherwise the root
    fix would corrupt the very path it was meant to protect.
    """
    once = request_mod.build_stream_payload(
        config, "hi", "conv-1", files=[IMAGE]
    )["files"]
    twice = request_mod.build_stream_payload(
        config, "hi", "conv-1", files=once
    )["files"]

    assert once == twice, "double normalization changed the payload"


def test_builder_omits_files_key_when_nothing_is_attachable(config):
    """
    An attachment with no resolvable URL is dropped by the normalizer. The
    builder must then omit `files` entirely rather than send an empty list.
    """
    payload = request_mod.build_stream_payload(
        config, "hi", "conv-1", files=[{"name": "no-url.txt"}]
    )

    assert "files" not in payload


def test_builder_without_attachments_is_unchanged(config):
    """No attachments must produce no `files` key at all."""
    assert "files" not in request_mod.build_stream_payload(config, "hi", "conv-1")
