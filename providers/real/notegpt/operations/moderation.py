# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Operation — Moderation / Safety  [STUB — NOT IMPLEMENTED]
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §6.2 (operations/)
POLICY : 01_31_PROVIDER_SCAFFOLDING_AND_ONBOARDING.md §12
         "Each template must mark unsupported modules as not implemented or
          not applicable, NOT as TODOs that imply mandatory work."

MANIFEST STATE : capabilities.moderation = unknown
EVIDENCE       : No evidence in any source. No moderation endpoint appears in the HAR, and no content-rejection app code has been observed among the verified codes (100000 / 164019 / 164003 / 164002).

WHY THIS FILE IS EMPTY
----------------------
No category taxonomy and no confidence scale are known, so there is nothing to
map onto the normalized content_rejected category.

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


def moderate_content(config: NoteGPTConfig, request: Dict[str, Any]) -> Dict[str, Any]:
    """NOT IMPLEMENTED — returns the normalized unsupported_capability error."""
    return {"error": err.unsupported_capability("moderate_content").to_dict()}
