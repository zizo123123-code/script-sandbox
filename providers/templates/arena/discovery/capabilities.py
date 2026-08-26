# -*- coding: utf-8 -*-
"""Capability shape for the Arena.ai Type L template.

True values describe the future provider category, not current availability.
`supports()` remains false because template_disabled providers are never
routable.
"""

from __future__ import annotations

from typing import Any, Dict

CAPABILITIES: Dict[str, Any] = {
    "chat": False,
    "text_generation": False,
    "reasoning": False,
    "code": False,
    "vision_input": False,
    "image_generation": False,
    "audio_input": False,
    "audio_output": False,
    "embeddings": False,
    "rerank": False,
    "moderation": False,
    "provider_agent": True,
    "tool_use": True,
    "files": True,
}


def get_capabilities() -> Dict[str, Any]:
    return dict(CAPABILITIES)


def supports(name: str) -> bool:
    """Capability declarations never bypass the template activation gate."""
    return False


def get_capabilities_with_evidence() -> Dict[str, Dict[str, Any]]:
    return {
        name: {
            "declared": value,
            "state": "TEMPLATE_ONLY" if value else "NOT_DECLARED",
            "evidence": "provider template shape only" if value else "none",
        }
        for name, value in CAPABILITIES.items()
    }
