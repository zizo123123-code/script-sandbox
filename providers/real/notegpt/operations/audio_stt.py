# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Operation — Audio Speech-to-Text  [STUB — NOT IMPLEMENTED]
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §6.2 (operations/)
POLICY : 01_31_PROVIDER_SCAFFOLDING_AND_ONBOARDING.md §12
         "Each template must mark unsupported modules as not implemented or
          not applicable, NOT as TODOs that imply mandatory work."

MANIFEST STATE : capabilities.speech_to_text = unknown
EVIDENCE       : CORRECTIONS.md final table: Audio / STT = UNKNOWN. The original capabilities.md inferred STT from YouTube-summary audio, which is not evidence of an STT API for arbitrary input.

WHY THIS FILE IS EMPTY
----------------------
No upload path, no transcription endpoint, and no result schema are known.
YouTube transcript retrieval (which IS confirmed) happens through the sandbox
`fetch_url` tool during an agent run — that is a different mechanism and is
already covered by operations/provider_agent.py.

30 §5  : "A provider implements only the operations it declares."
30 §17 : "Provider functionality must never be faked."

The file exists so the architecture stays structurally complete (§6.2). It
returns `unsupported_capability` rather than a stub result, so the router
treats this provider as ineligible for the task instead of receiving a fake
success. If evidence later appears, implement here and flip the manifest.
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict

from .. import errors as err
from ..config import NoteGPTConfig

SUPPORTED = False
CAPABILITY_STATE = "unknown"


def transcribe_audio(config: NoteGPTConfig, request: Dict[str, Any]) -> Dict[str, Any]:
    """NOT IMPLEMENTED — returns the normalized unsupported_capability error."""
    return {"error": err.unsupported_capability("transcribe_audio").to_dict()}
