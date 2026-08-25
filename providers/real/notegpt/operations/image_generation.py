# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Operation — Image Generation  [STUB — NOT IMPLEMENTED]
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §6.2 (operations/)
POLICY : 01_31_PROVIDER_SCAFFOLDING_AND_ONBOARDING.md §12
         "Each template must mark unsupported modules as not implemented or
          not applicable, NOT as TODOs that imply mandatory work."

MANIFEST STATE : capabilities.image_generation = unknown
EVIDENCE       : CORRECTIONS.md final table: Image Generation = UNKNOWN. The original provider_summary.md claimed AVAILABLE_BUT_NOT_IMPLEMENTED based on the website UI, but no image endpoint appears in any of the 916 HAR entries and no request shape is known.

WHY THIS FILE IS EMPTY
----------------------
There is no endpoint, no payload schema, and no response shape to implement
against. Writing a speculative client would be inventing an API — explicitly
forbidden by 31 §4 ("invent API endpoints").

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


def generate_image(config: NoteGPTConfig, request: Dict[str, Any]) -> Dict[str, Any]:
    """NOT IMPLEMENTED — returns the normalized unsupported_capability error."""
    return {"error": err.unsupported_capability("generate_image").to_dict()}
