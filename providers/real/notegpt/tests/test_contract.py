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

import os
import sys
from pathlib import Path

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
def test_capabilities_are_tri_state():
    """CORRECTIONS.md §13 — unevidenced capabilities are 'unknown', never False."""
    caps = caps_mod.get_capabilities()
    for name, value in caps.items():
        assert value is True or value == "unknown", (
            f"capability '{name}' must be True or 'unknown', got {value!r}"
        )


def test_confirmed_capabilities_have_evidence():
    detailed = caps_mod.get_capabilities_with_evidence()
    for name, info in detailed.items():
        if info["state"] == "CONFIRMED":
            assert info["evidence"], f"CONFIRMED capability '{name}' lacks evidence"


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
    """
    package_root = Path(__file__).resolve().parents[1]
    offenders = []
    for path in package_root.rglob("*.py"):
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for marker in ('PASSWORD: str = "', 'SESSION_TOKEN: str = "', 'EMAIL: str = "'):
            if marker in text:
                offenders.append(f"{path.name}: {marker}")
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
