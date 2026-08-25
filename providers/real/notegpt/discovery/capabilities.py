# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Discovery — Capabilities
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §4.1, §8.1
SOURCE : inventory/notegpt/CORRECTIONS.md "خلاصة الحالات المصححة"

THREE-VALUE MODEL
-----------------
CORRECTIONS.md §13 established the rule that governs this file:
    absence of evidence is NOT evidence of absence.

So capabilities are tri-state, never boolean-by-default:
    True      — CONFIRMED, traceable to a code line or HAR count
    "unknown" — no evidence either way; provider MAY support it
    False     — only where the platform genuinely does not expose it

This is why `video_generation` is "unknown" and not False: the original
provider_summary.md marked it CONFIRMED_UNSUPPORTED, but §13 requires
conclusive proof for a negative claim, and none exists.
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
    "vision_input": "image_recognition tool · 01.05:1076",
    "file_upload": "native files[] payload · 01.06:759",
    "provider_agent": "Daytona sandbox lifecycle · 01.05:745-911",
    "tool_use": "fetch_url / web_search · 01.05:1078",
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


def get_capabilities() -> Dict[str, Any]:
    """Tri-state capability map — 30 §8.1 getCapabilities()."""
    caps: Dict[str, Any] = {}
    for name in CONFIRMED:
        caps[name] = True
    for name in UNKNOWN:
        caps[name] = "unknown"
    return caps


def get_capabilities_with_evidence() -> Dict[str, Dict[str, Any]]:
    """Capability map annotated with its evidence trail, for audit/admin."""
    detailed: Dict[str, Dict[str, Any]] = {}
    for name, evidence in CONFIRMED.items():
        detailed[name] = {"supported": True, "state": "CONFIRMED", "evidence": evidence}
    for name, note in UNKNOWN.items():
        detailed[name] = {"supported": "unknown", "state": "UNKNOWN", "evidence": note}
    for name, note in NOT_IMPLEMENTED.items():
        detailed[name] = {"supported": False, "state": "NOT_IMPLEMENTED", "evidence": note}
    return detailed


def supports(capability: str) -> bool:
    """
    Strict check for routing. "unknown" returns False here: the router must
    not gamble on an unevidenced capability, even though the provider may
    in fact support it.
    """
    return capability in CONFIRMED


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
