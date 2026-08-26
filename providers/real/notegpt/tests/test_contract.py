# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Provider — Contract Tests
================================================================================
SPEC : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §18.1, §18.3, §18.4
       01_31_PROVIDER_SCAFFOLDING_AND_ONBOARDING.md §11

SCOPE RULE (31 §11): "Do not write tests that pretend generation works."

These tests verify the CONTRACT — manifest validity, capability declarations,
error normalization, unsupported-operation rejection, secret redaction, and the
model catalog. They make no network calls.

Live generation tests require real credentials and are therefore explicitly
absent, not silently faked. That absence is exactly why manifest status stays
`disabled` (31 §19.13).

Run:  python3 -m pytest providers/real/notegpt/tests/ -v
      python3 providers/real/notegpt/tests/test_contract.py     (no pytest)
================================================================================
"""

from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from providers.real.notegpt import errors as err                        # noqa: E402
from providers.real.notegpt.config import NoteGPTConfig                 # noqa: E402
from providers.real.notegpt.discovery import capabilities as caps_mod   # noqa: E402
from providers.real.notegpt.discovery import limits as limits_mod       # noqa: E402
from providers.real.notegpt.discovery import models as models_mod       # noqa: E402
from providers.real.notegpt.provider import NoteGPTProvider             # noqa: E402
from providers.real.notegpt.runtime import parser as parser_mod         # noqa: E402


# ==============================================================================
# 18.1 — Manifest schema validation
# ==============================================================================
def test_manifest_has_required_identity_fields():
    m = NoteGPTProvider().get_manifest()
    for field in ("id", "name", "status", "is_template", "is_functional"):
        assert field in m, f"manifest missing required field: {field}"
    assert m["id"] == "notegpt"


def test_manifest_is_not_a_template():
    """31 §18 — a real provider must not carry template markers."""
    m = NoteGPTProvider().get_manifest()
    assert m.get("is_template") is False
    assert m.get("real_provider_required") is False


def test_provider_is_disabled_until_verified():
    """31 §19.13 / §22 — no activation before contract tests + security review."""
    m = NoteGPTProvider().get_manifest()
    assert m.get("status") in {"disabled", "maintenance"}, (
        "Provider must not be 'active' while live contract tests are absent."
    )
    assert m.get("is_functional") is False


# ==============================================================================
# 18.1 — Capability declaration validation
# ==============================================================================
def test_capabilities_are_never_bare_false():
    """
    CORRECTIONS.md §13 — unevidenced capabilities are 'unknown', never False.
    T-04 adds 'partial' for features that exist upstream but are blocked here.

    (Renamed from `test_capabilities_are_tri_state`: the model is four-state
    since T-04, and a test name that says "tri" would mislead the next reader.)
    """
    caps = caps_mod.get_capabilities()
    allowed = (True, caps_mod.PARTIAL_VALUE, "unknown")
    for name, value in caps.items():
        assert value in allowed, (
            f"capability '{name}' must be one of {allowed}, got {value!r}"
        )


def test_confirmed_capabilities_have_evidence():
    detailed = caps_mod.get_capabilities_with_evidence()
    for name, info in detailed.items():
        if info["state"] == "CONFIRMED":
            assert info["evidence"], f"CONFIRMED capability '{name}' lacks evidence"


# ==============================================================================
# T-04 — capability honesty: manifest and code are ONE contract
# ==============================================================================
def test_blocked_capabilities_are_partial_not_true():
    """
    THE regression this guards: `file_upload` and `vision_input` were `True`
    while `upload_asset()` always returns UNSUPPORTED_CAPABILITY. A True in
    front of an operation that cannot complete is faked functionality
    (30 §17 / 31 §4).
    """
    caps = caps_mod.get_capabilities()
    for name in ("file_upload", "vision_input"):
        assert caps[name] == "partial", (
            f"'{name}' must be 'partial' — the upload path is blocked"
        )
        assert caps_mod.is_partial(name)
        assert name not in caps_mod.CONFIRMED, f"'{name}' must not be CONFIRMED"


def test_every_partial_capability_names_a_blocker():
    """A 'partial' with no blocker is just a True in disguise."""
    detailed = caps_mod.get_capabilities_with_evidence()
    partials = [n for n, i in detailed.items() if i["state"] == "PARTIALLY_SUPPORTED"]
    assert partials, "expected at least one PARTIALLY_SUPPORTED capability"
    for name in partials:
        assert detailed[name]["blocker"], f"partial '{name}' lacks a named blocker"
        assert caps_mod.get_blocker(name), f"get_blocker('{name}') returned nothing"


def test_partial_capability_is_not_routable():
    """`supports()` gates routing: a blocked capability must never pass it."""
    assert caps_mod.supports("file_upload") is False
    assert caps_mod.supports("vision_input") is False
    assert caps_mod.supports("chat") is True


def test_manifest_capabilities_match_code_exactly():
    """
    T-04 — the manifest and discovery/capabilities.py must not drift. This is
    the test that makes them a single contract rather than two copies.
    """
    manifest_caps = NoteGPTProvider().get_manifest().get("capabilities")
    if not manifest_caps:
        pytest.skip("PyYAML unavailable — manifest not parsed")
    code_caps = caps_mod.get_capabilities()
    assert manifest_caps == code_caps, (
        "manifest.yaml and capabilities.py disagree: "
        f"{ {k: (manifest_caps.get(k), code_caps.get(k)) for k in set(manifest_caps) | set(code_caps) if manifest_caps.get(k) != code_caps.get(k)} }"
    )


def test_manifest_declares_blocker_for_each_partial():
    """Every `partial` in the manifest carries a machine-readable blocker."""
    manifest = NoteGPTProvider().get_manifest()
    caps = manifest.get("capabilities")
    if not caps:
        pytest.skip("PyYAML unavailable — manifest not parsed")
    blockers = manifest.get("capabilities_blockers", {})
    for name, value in caps.items():
        if value == "partial":
            assert name in blockers, f"manifest '{name}' is partial with no blocker"
            assert blockers[name].get("blocker"), f"'{name}' blocker is empty"


def test_upload_operation_stays_declared_while_capability_is_partial():
    """
    The deliberate asymmetry: the OPERATION is reachable (so callers get a
    normalized error naming the blocker) while the CAPABILITY is honest about
    being incomplete. Undeclaring the operation would be a different signal.
    """
    manifest = NoteGPTProvider().get_manifest()
    ops = manifest.get("operations")
    if not ops:
        pytest.skip("PyYAML unavailable — manifest not parsed")
    assert ops["upload_asset"] is True
    assert manifest["capabilities"]["file_upload"] == "partial"


def test_upload_asset_error_matches_declared_blocker():
    """The runtime error must name the same blocker the manifest declares."""
    from providers.real.notegpt.assets import upload as upload_mod

    result = upload_mod.upload_asset(NoteGPTConfig(), {"file": "/tmp/x.png"})
    assert result["error"]["category"] == err.UNSUPPORTED_CAPABILITY
    official = result["error"]["details"]["official_path"]
    assert official["blocker"] == caps_mod.get_blocker("file_upload")


def test_video_generation_is_unknown_not_false():
    """
    The original provider_summary.md claimed CONFIRMED_UNSUPPORTED.
    CORRECTIONS.md §13 requires conclusive proof for a negative claim.
    """
    assert caps_mod.is_unknown("video_generation")


def test_account_pool_not_declared_supported():
    """CORRECTIONS.md §7 — the pool was claimed but never existed."""
    m = NoteGPTProvider().get_manifest()
    pool = m.get("account_pool", {})
    assert pool.get("supported") is False
    assert pool.get("lease_required") is False


# ==============================================================================
# 18.1 — Unsupported operations rejected
# ==============================================================================
def test_undeclared_operations_are_rejected():
    """30 §5 — an undeclared operation makes the provider ineligible."""
    provider = NoteGPTProvider()
    for operation in (
        "generate_image",
        "transcribe_audio",
        "synthesize_speech",
        "create_embeddings",
        "rerank_documents",
        "moderate_content",
    ):
        result = provider.generate({"operation": operation, "prompt": "x"})
        assert "error" in result, f"{operation} should be rejected"
        assert result["error"]["category"] == err.UNSUPPORTED_CAPABILITY


def test_unknown_operation_name_is_rejected():
    result = NoteGPTProvider().generate({"operation": "definitely_not_real"})
    assert result["error"]["category"] == err.UNSUPPORTED_CAPABILITY


def test_agent_run_handle_operations_are_unsupported():
    """No thread/run API exists — conversation_id is the only state handle."""
    provider = NoteGPTProvider()
    assert provider.get_agent_run("x")["error"]["category"] == err.UNSUPPORTED_CAPABILITY
    assert provider.cancel_agent_run("x")["error"]["category"] == err.UNSUPPORTED_CAPABILITY
    assert provider.create_agent_run({})["error"]["category"] == err.UNSUPPORTED_CAPABILITY


def test_disabled_provider_blocks_declared_operations():
    """The activation gate must block even DECLARED operations while disabled."""
    from providers.real.notegpt.provider import ProviderDisabledError

    provider = NoteGPTProvider()
    try:
        provider.generate({"operation": "generate_text", "prompt": "hello"})
    except ProviderDisabledError:
        return
    raise AssertionError("disabled provider must not execute generate_text")


# ==============================================================================
# 18.1 / 18.3 — Error normalization
# ==============================================================================
def test_all_categories_are_from_the_spec_list():
    assert len(err.ALL_CATEGORIES) == 12


def test_success_code_is_100000_not_zero():
    """CORRECTIONS.md §3 — code:0 appears zero times in 916 HAR entries."""
    assert err.is_success_code(100000) is True
    assert err.is_success_code(0) is False


def test_app_code_wins_over_http_200():
    """
    THE critical behavior: an expired session arrives as HTTP 200 with
    {"code": 164003}. Normalization must not read that as success.
    """
    normalized = err.normalize_error(
        http_status=200, body={"code": 164003, "message": "login expired"}
    )
    assert normalized.category == err.AUTH_EXPIRED
    assert normalized.retryable is True
    assert normalized.details["source"] == "app_code"


def test_quota_exceeded_maps_to_rotation():
    normalized = err.normalize_error(http_status=200, body={"code": 164019})
    assert normalized.category == err.QUOTA_EXCEEDED
    assert normalized.details["recovery"] == "rotate_identity"


def test_all_three_auth_codes_recover_by_rotation():
    """
    01.06:798 groups all three codes into ONE branch that calls
    rotate_identity(keep_conversation=True) — it never calls login().

    The category still reflects MEANING (auth vs quota), but the recovery hint
    must reflect observed BEHAVIOR, with reauthenticate kept as an unverified
    fallback. This test exists because the first implementation asserted
    'reauthenticate' for 164003/164002, which the reference code contradicts.
    """
    for code in (164019, 164003, 164002):
        normalized = err.normalize_error(body={"code": code})
        assert normalized.details["recovery"] == "rotate_identity", (
            f"code {code} must recover by rotation per 01.06:798"
        )


def test_auth_codes_keep_reauth_as_unverified_fallback():
    for code in (164003, 164002):
        details = err.normalize_error(body={"code": code}).details
        assert details.get("recovery_fallback") == "reauthenticate"


def test_mapped_app_codes_carry_evidence():
    for code in err.APP_CODE_MAP:
        details = err.normalize_error(body={"code": code}).details
        assert details.get("evidence"), f"mapped code {code} lacks an evidence tag"


def test_auth_and_quota_codes_keep_distinct_categories():
    """Shared recovery must not collapse the semantic distinction."""
    assert err.normalize_error(body={"code": 164019}).category == err.QUOTA_EXCEEDED
    assert err.normalize_error(body={"code": 164003}).category == err.AUTH_EXPIRED
    assert err.normalize_error(body={"code": 164002}).category == err.INVALID_CREDENTIAL


def test_unmapped_app_code_is_not_guessed():
    normalized = err.normalize_error(body={"code": 999999})
    assert normalized.category == err.NON_RETRYABLE_ERROR
    assert normalized.details["evidence"] == "none"


def test_success_body_produces_no_error_category():
    normalized = err.normalize_error(http_status=200, body={"code": 100000})
    # No app-code error -> falls through; must not report a false auth failure.
    assert normalized.category == err.NON_RETRYABLE_ERROR
    assert normalized.details["source"] == "none"


def test_unmapped_http_status_marked_unevidenced():
    """429/403/504 have zero occurrences — they must be tagged as such."""
    for status in (429, 403, 504):
        normalized = err.normalize_error(http_status=status)
        assert normalized.details["evidence"] == "none"


def test_stream_error_events_normalize():
    assert err.normalize_error(stream_event="error").category == err.NON_RETRYABLE_ERROR
    assert err.normalize_error(stream_event="length").details["recovery"] == "auto_continue"


def test_invalid_category_is_rejected():
    try:
        err.ProviderError(
            category="not_a_real_category",
            retryable=False,
            provider_code="x",
            safe_message="x",
        )
    except ValueError:
        return
    raise AssertionError("ProviderError must reject non-spec categories")


# ==============================================================================
# 18.3 — Model discovery
# ==============================================================================
def test_catalog_has_36_models():
    assert len(models_mod.load_catalog()) == 36


def test_phantom_models_are_excluded():
    """CORRECTIONS.md §6 — the 7 invented models must never be routable."""
    ids = set(models_mod.list_model_ids())
    for phantom in models_mod.PHANTOM_MODELS:
        assert phantom not in ids, f"phantom model leaked into bindings: {phantom}"


def test_phantom_model_request_is_rejected_with_reason():
    resolution = models_mod.resolve_model("claude-3-7-sonnet")
    assert resolution["resolved"] is False
    assert resolution["reason"] == "phantom_model"


def test_default_model_is_valid():
    assert models_mod.is_valid_model(models_mod.DEFAULT_MODEL)


def test_only_two_reasoning_models():
    """Only these carry think=true in the catalog."""
    assert set(models_mod.get_reasoning_models()) == {
        "deepseek-reasoner",
        "TA/deepseek-ai/DeepSeek-R1",
    }


def test_per_model_modality_is_unknown():
    """ROUND2 §5 — the catalog has no vision field; claims were guesses."""
    for binding in models_mod.discover_models():
        assert binding["capabilities"]["vision_input"] == "unknown"


# ==============================================================================
# 18.3 — SSE parsing (ROUND2 §2)
# ==============================================================================
def test_all_13_events_plus_alias_known():
    assert len(parser_mod.KNOWN_EVENTS) == 14   # 13 + tool_result alias


def test_text_event_is_present():
    """
    ROUND2 §2: `text` was missing from every original doc AND from the first
    corrections pass. It carries the answer — losing it loses the response.
    """
    assert parser_mod.EVENT_TEXT in parser_mod.KNOWN_EVENTS
    events = list(parser_mod.iter_events(['data: {"type":"text","text":"hello"}']))
    assert any(e["type"] == "text" and e["content"] == "hello" for e in events)


def test_done_sentinel_parsed():
    events = list(parser_mod.iter_events(["data: [DONE]"]))
    assert events[0]["type"] == parser_mod.EVENT_DONE


def test_done_with_length_reason_becomes_continue_needed():
    events = list(parser_mod.iter_events(['data: {"type":"done","reason":"length"}']))
    assert events[0]["type"] == parser_mod.EVENT_CONTINUE_NEEDED


def test_rotation_code_in_stream_flagged():
    events = list(parser_mod.iter_events(['data: {"code":164019}']))
    assert events[0]["subtype"] == "identity_rotation_required"


def test_tool_result_alias_normalized():
    events = list(parser_mod.iter_events(['data: {"type":"tool_result","output":"ok"}']))
    assert events[0]["type"] == parser_mod.EVENT_TOOL_CALL_RESULT


def test_malformed_json_is_surfaced_not_swallowed():
    events = list(parser_mod.iter_events(["data: {not valid json"]))
    assert events[0]["type"] == parser_mod.EVENT_ERROR


def test_platform_event_mapping():
    """30 §15.3 — raw provider semantics must not leak to the Core."""
    mapped = parser_mod.to_platform_event({"type": "tool_call", "tool": "bash"})
    assert mapped["event"] == "provider_agent.tool_requested"


# ==============================================================================
# 18.3 — Rate limits
# ==============================================================================
def test_fabricated_limits_are_unknown():
    """CORRECTIONS.md §7 — these five numbers had no source."""
    unknown = limits_mod.get_limits()["unknown"]
    for key in (
        "daily_quota",
        "requests_per_minute",
        "cooldown_seconds",
        "quota_reset_time",
        "context_window",
    ):
        assert key in unknown, f"{key} must be reported as unknown"


def test_auto_continue_limit_is_five():
    assert limits_mod.AUTO_CONTINUE_LIMIT == 5
    assert limits_mod.should_auto_continue(4) is True
    assert limits_mod.should_auto_continue(5) is False


def test_quota_code_maps_to_limited_state():
    state = limits_mod.normalize_limit_state(app_code=164019)
    assert state["state"] == limits_mod.STATE_LIMITED
    assert state["recovery"] == "rotate_identity"


# ==============================================================================
# 18.3 — No secret leakage in logs
# ==============================================================================
def test_config_repr_never_contains_credentials():
    """30 §18.3 — 'no secret leakage in logs'."""
    os.environ["NOTEGPT_EMAIL"] = "canary-email@example.test"
    os.environ["NOTEGPT_PASSWORD"] = "CanaryPassword123"
    os.environ["NOTEGPT_SESSION_TOKEN"] = "canary-token-value"
    try:
        config = NoteGPTConfig()
        for rendered in (repr(config), str(config), str(config.redacted())):
            assert "canary-email@example.test" not in rendered
            assert "CanaryPassword123" not in rendered
            assert "canary-token-value" not in rendered
        assert config.redacted()["has_password"] is True
    finally:
        for key in ("NOTEGPT_EMAIL", "NOTEGPT_PASSWORD", "NOTEGPT_SESSION_TOKEN"):
            os.environ.pop(key, None)


def test_no_hardcoded_credentials_in_package():
    """
    ROUND2 §0 found 29 secrets across 10 files in projects/ngpt/.
    This test guards THIS package against repeating that.

    P1 — this guard USED TO look only for the class-attribute spelling
    (`PASSWORD: str = "..."`). A live session token, email and password sat in
    `__main__.py` written as `os.environ["NOTEGPT_PASSWORD"] = "..."` and the
    guard passed, because that form contains none of the three markers. A
    substring list can only ever catch the spellings someone thought of, so the
    check now parses the file and inspects assignment TARGETS — every way of
    writing an assignment reduces to the same AST.
    """
    package_root = Path(__file__).resolve().parents[1]

    sensitive = re.compile(r"PASSWORD|PASSWD|PWD|TOKEN|SECRET|API_?KEY|EMAIL", re.I)
    # RFC 2606 / RFC 6761 reserved domains + self-declaring test values.
    test_value = re.compile(
        r"canary|probe|dummy|placeholder|fixture|fake|mock|example|"
        r"\.(?:test|invalid|example|localhost)\b",
        re.I,
    )

    def target_names(node):
        """Every name/string a value is being assigned INTO."""
        for tgt in getattr(node, "targets", []):
            if isinstance(tgt, ast.Name):
                yield tgt.id
            elif isinstance(tgt, ast.Attribute):
                yield tgt.attr
            elif isinstance(tgt, ast.Subscript):
                # os.environ["NOTEGPT_PASSWORD"] = "..."  <-- the missed form
                key = tgt.slice
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    yield key.value

    offenders = []
    for path in package_root.rglob("*.py"):
        if "tests" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = getattr(node, "value", None)
            # Only literal strings are secrets; `X = os.environ[...]` is a Call
            # or Subscript node and is correctly ignored.
            if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                continue
            if len(value.value) < 3 or test_value.search(value.value):
                continue
            # An env-var NAME is not a credential VALUE. `config.py` legitimately
            # declares `ENV_PASSWORD = "NOTEGPT_PASSWORD"` — that constant is the
            # very mechanism that keeps secrets OUT of the source, so flagging it
            # would punish the correct pattern. Distinguished structurally (the
            # value is itself a bare SCREAMING_SNAKE identifier), not by trusting
            # a file name: a real password would have to consist solely of
            # uppercase, digits and underscores to slip through here.
            if re.fullmatch(r"[A-Z][A-Z0-9_]*", value.value):
                continue
            names = list(target_names(node)) if isinstance(node, ast.Assign) else []
            if isinstance(node, ast.AnnAssign):
                tgt = node.target
                if isinstance(tgt, ast.Name):
                    names = [tgt.id]
                elif isinstance(tgt, ast.Attribute):
                    names = [tgt.attr]
            for name in names:
                if sensitive.search(name):
                    offenders.append(f"{path.name}:{node.lineno} -> {name}")

    assert not offenders, f"hardcoded credentials found: {offenders}"


def test_config_reads_credentials_from_env_only():
    config = NoteGPTConfig()
    source = Path(config.__class__.__module__.replace(".", "/") + ".py")
    assert config.has_credentials in (True, False)   # never raises
    assert "os.environ" in (Path(__file__).resolve().parents[1] / "config.py").read_text(
        encoding="utf-8"
    )


# ==============================================================================
# 18.1 — Core isolation
# ==============================================================================
def test_provider_exposes_only_the_adapter():
    """30 §2 — 'Core must not import provider internals'."""
    import providers.real.notegpt as pkg

    assert pkg.__all__ == ["NoteGPTProvider", "get_provider"]


def test_required_adapter_interface_present():
    """30 §8.1 — every required method must exist."""
    provider = NoteGPTProvider()
    for method in (
        "get_manifest",
        "validate_credential",
        "discover_models",
        "get_capabilities",
        "generate",
        "health_check",
        "normalize_error",
    ):
        assert callable(getattr(provider, method, None)), f"missing: {method}"


def test_health_reports_suspended_while_disabled():
    health = NoteGPTProvider().health_check()
    assert health["state"] == "SUSPENDED"
    assert health["checked_live"] is False


def test_validate_credential_without_env_is_safe():
    for key in ("NOTEGPT_EMAIL", "NOTEGPT_PASSWORD", "NOTEGPT_SESSION_TOKEN"):
        os.environ.pop(key, None)
    result = NoteGPTProvider(NoteGPTConfig()).validate_credential()
    assert result["valid"] is False
    assert result["checked_live"] is False


# ==============================================================================
# Standalone runner (no pytest required)
# ==============================================================================
def _run_all() -> int:
    tests = [(n, o) for n, o in sorted(globals().items())
             if n.startswith("test_") and callable(o)]
    passed, failed = 0, []
    for name, fn in tests:
        try:
            fn()
            passed += 1
            print(f"  PASS  {name}")
        except AssertionError as exc:
            failed.append((name, f"AssertionError: {exc}"))
            print(f"  FAIL  {name} -> {exc}")
        except Exception as exc:  # noqa: BLE001
            failed.append((name, f"{type(exc).__name__}: {exc}"))
            print(f"  ERROR {name} -> {type(exc).__name__}: {exc}")

    print(f"\n{'=' * 70}")
    print(f"total={len(tests)}  passed={passed}  failed={len(failed)}")
    print("=" * 70)
    if failed:
        for name, reason in failed:
            print(f"  - {name}: {reason}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_run_all())
