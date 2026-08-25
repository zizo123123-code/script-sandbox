# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Operation — Vision Analysis
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §5 (analyze_vision)
SOURCE : inventory/notegpt/CORRECTIONS.md §10 · upload.md §2
         projects/ngpt/scripts/01.05:1076 (image_recognition tool)

DECLARED: capabilities.vision_input = CONFIRMED

IMPLEMENTATION NOTE — why this file delegates
---------------------------------------------
NoteGPT exposes NO dedicated vision endpoint. Vision works like this:
    1. the image is attached in the native files[] payload
    2. the sandbox receives it and the model is given an `image_recognition`
       tool (01.05:1076)
    3. the model calls that tool itself during the agent run

So vision is not a separate transport — it is the agent path with an image
attached. Duplicating the stream logic here would be dead code, so this module
validates the vision-specific inputs and delegates.
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict, List

from .. import errors as err
from ..config import NoteGPTConfig

# upload.md claimed PNG/JPG/WEBP + PDF/TXT/MD/CSV, but CORRECTIONS.md §5 marks
# supported formats UNKNOWN (the code does not restrict them). We therefore do
# not reject formats here -- rejecting on a guessed list would block valid input.
SUPPORTED_FORMATS = "unknown"
MAX_FILE_SIZE = "unknown"


def analyze_vision(config: NoteGPTConfig, request: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze image(s) via the sandbox `image_recognition` tool."""
    images: List[Any] = request.get("images") or request.get("files") or []
    if not images:
        return {
            "error": err.ProviderError(
                category=err.BAD_REQUEST,
                retryable=False,
                provider_code="no_image_provided",
                safe_message="analyze_vision requires at least one image.",
            ).to_dict()
        }

    from . import provider_agent

    forwarded = dict(request)
    forwarded["files"] = images
    forwarded.setdefault(
        "prompt",
        "Analyze the attached image(s) using the image_recognition tool.",
    )
    return provider_agent.run_provider_agent(config, forwarded)
