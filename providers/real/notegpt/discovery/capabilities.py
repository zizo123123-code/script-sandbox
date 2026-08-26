# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Discovery — Capabilities
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §4.1, §8.1
SOURCE : inventory/notegpt/CORRECTIONS.md "خلاصة الحالات المصححة"

FOUR-VALUE MODEL
----------------
CORRECTIONS.md §13 established the rule that governs this file:
    absence of evidence is NOT evidence of absence.

So capabilities are never boolean-by-default:
    True        — CONFIRMED, traceable to a code line or HAR count
    "partial"   — the feature EXISTS upstream but cannot be completed by this
                  package because of a named, documented blocker
    "unknown"   — no evidence either way; provider MAY support it
    False       — only where the platform genuinely does not expose it

This is why `video_generation` is "unknown" and not False: the original
provider_summary.md marked it CONFIRMED_UNSUPPORTED, but §13 requires
conclusive proof for a negative claim, and none exists.

WHY "partial" WAS ADDED (T-04)
------------------------------
`file_upload` and `vision_input` were declared `True`, which claimed a working
end-to-end feature. They are not. Both depend on getting bytes into the
provider, and that path is blocked:

    official path  POST /api/v1/upload/sign-url -> Alibaba OSS
                   requires an HMAC `sign` field whose derivation is
                   undocumented (CORRECTIONS.md §5 — "the single most
                   important technical obstacle"). Not implementable.
    only path that
    actually works tmpfiles.org, a PUBLIC third-party host, refused as a
                   default under 30 §15.4 (tenant isolation).

`assets/upload.upload_asset()` therefore returns UNSUPPORTED_CAPABILITY unless
the caller explicitly opts into third-party transit. A capability flag of True
in front of an operation that always errors is exactly the "faking
functionality" that 30 §17 / 31 §4 forbid, so the honest value is "partial":
the operation is DECLARED and reachable, the capability is NOT complete.

Note the asymmetry this encodes on purpose:
    operations.upload_asset  = true      (the entry point exists and responds)
    capabilities.file_upload = "partial" (it cannot actually deliver a file)
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict

# --- CONFIRMED capabilities, with evidence ---------------------------------
CONFIRMED: Dict[str, str] = {
    "chat": "POST /api/v2/chat/stream · HAR x62",
    "text_generation": "01.06:739 ask_agent_stream",
    "streaming": "SSE, 13 event types · CORRECTIONS_ROUND2.md §2",
    "reasoning": "deepseek-reasoner + DeepSeek-R1 (think=true in catalog)",
    "code": "sandbox executes python3 / bash via tool_call",
    "provider_agent": "Daytona sandbox lifecycle · 01.05:745-911",
    "tool_use": "fetch_url / web_search · 01.05:1078",
}

# --- PARTIAL — feature exists upstream, blocked here (T-04) -----------------
# Each entry MUST name its blocker. A blocker-less "partial" is just a True in
# disguise, so `get_capabilities_with_evidence()` refuses to emit one.
PARTIAL: Dict[str, Dict[str, str]] = {
    "file_upload": {
        "evidence": "native files[] payload · 01.06:759 (the SEND side works)",
        "blocker": "hmac_sign_field_undocumented",
        "detail": (
            "Attachments can be referenced in the request body, but this package "
            "cannot produce the file URL: the official sign-url path needs an "
            "undocumented HMAC (CORRECTIONS.md §5) and the only working path "
            "transits tmpfiles.org, a public third-party host (ROUND2 §3). "
            "upload_asset() returns UNSUPPORTED_CAPABILITY without an explicit "
            "allow_third_party_transit opt-in."
        ),
    },
    "vision_input": {
        "evidence": "image_recognition tool · 01.05:1076 (tool is real)",
        "blocker": "depends_on_blocked_file_upload",
        "detail": (
            "The sandbox tool exists, but it consumes an image URL that only the "
            "blocked upload path can produce. ROUND2 §5 additionally records that "
            "the catalog has no per-model vision field, so no model can be "
            "confirmed multimodal (see models.discover_models -> 'unknown')."
        ),
    },
}

# --- UNKNOWN — no traceable evidence in code, catalog, or 916 HAR entries ---
UNKNOWN: Dict[str, str] = {
    "image_generation": "UI reportedly supports it; no endpoint evidence",
    "audio_input": "no evidence",
    "audio_output": "no evidence",
    "speech_to_text": "no evidence",
    "text_to_speech": "no evidence",
    "embeddings": "no endpoint in available HAR",
    "rerank": "no evidence",
    "moderation": "no evidence",
    "video_generation": "was falsely CONFIRMED_UNSUPPORTED; §13 needs proof",
    "browser": "web_search exists, but browser automation is unevidenced",
}

# --- NOT_IMPLEMENTED — the platform may allow it, this provider does not ----
NOT_IMPLEMENTED: Dict[str, str] = {
    "account_pool": (
        "CORRECTIONS.md §7 — accounts_notegpt.json does not exist. "
        "rotate_identity() rotates IP + cookies on the same account only."
    ),
}


PARTIAL_VALUE = "partial"


def get_capabilities() -> Dict[str, Any]:
    """Four-state capability map — 30 §8.1 getCapabilities()."""
    caps: Dict[str, Any] = {}
    for name in CONFIRMED:
        caps[name] = True
    for name in PARTIAL:
        caps[name] = PARTIAL_VALUE
    for name in UNKNOWN:
        caps[name] = "unknown"
    return caps


def get_capabilities_with_evidence() -> Dict[str, Dict[str, Any]]:
    """Capability map annotated with its evidence trail, for audit/admin."""
    detailed: Dict[str, Dict[str, Any]] = {}
    for name, evidence in CONFIRMED.items():
        detailed[name] = {"supported": True, "state": "CONFIRMED", "evidence": evidence}
    for name, info in PARTIAL.items():
        # A "partial" without a blocker would silently read as "supported".
        detailed[name] = {
            "supported": PARTIAL_VALUE,
            "state": "PARTIALLY_SUPPORTED",
            "evidence": info["evidence"],
            "blocker": info["blocker"],
            "detail": info["detail"],
        }
    for name, note in UNKNOWN.items():
        detailed[name] = {"supported": "unknown", "state": "UNKNOWN", "evidence": note}
    for name, note in NOT_IMPLEMENTED.items():
        detailed[name] = {"supported": False, "state": "NOT_IMPLEMENTED", "evidence": note}
    return detailed


def supports(capability: str) -> bool:
    """
    Strict check for routing. Only CONFIRMED passes.

    "unknown" returns False: the router must not gamble on an unevidenced
    capability. "partial" ALSO returns False, and that is the whole point of
    T-04 — routing a job to a capability that cannot complete would surface as
    a runtime error to the tenant. Callers that can handle a degraded path must
    ask for it explicitly via `is_partial()`.
    """
    return capability in CONFIRMED


def is_partial(capability: str) -> bool:
    """True when the capability exists upstream but is blocked here."""
    return capability in PARTIAL


def get_blocker(capability: str) -> Any:
    """The named blocker for a partial capability, else None."""
    info = PARTIAL.get(capability)
    return info["blocker"] if info else None


def is_unknown(capability: str) -> bool:
    return capability in UNKNOWN


def get_provider_tools() -> Dict[str, str]:
    """Sandbox tools available to the native agent — CORRECTIONS.md §10."""
    return {
        "bash": "CONFIRMED — shell execution via tool_call",
        "python3": "CONFIRMED — python execution via tool_call",
        "image_recognition": "CONFIRMED — 01.05:1076",
        "fetch_url": "CONFIRMED — 01.05:1078",
        "web_search": "CONFIRMED — 01.05:1078",
    }


def get_sandbox_environment() -> Dict[str, str]:
    """
    Sandbox environment facts — CORRECTIONS.md §10.

    Every value the original agent.md asserted here turned out to be
    unevidenced: "Ubuntu 22.04" (grep -ci ubuntu = 0), "/home/daytona/",
    "Python 3.10+". They are reported as unknown rather than repeated.
    """
    return {
        "os": "unknown",
        "workdir": "unknown",
        "python_version": "unknown",
        "internet_access": "unknown",
    }
