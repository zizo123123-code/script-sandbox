# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Operation — Embeddings  [STUB — NOT IMPLEMENTED]
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §6.2 (operations/)
POLICY : 01_31_PROVIDER_SCAFFOLDING_AND_ONBOARDING.md §12
         "Each template must mark unsupported modules as not implemented or
          not applicable, NOT as TODOs that imply mandatory work."

MANIFEST STATE : capabilities.embeddings = unknown
EVIDENCE       : CORRECTIONS.md final table: Embeddings = UNKNOWN (the one capability the original capabilities.md tagged correctly). No embeddings endpoint in the available HAR.

WHY THIS FILE IS EMPTY
----------------------
Vector dimensions, batch behavior, and the model binding are all unknown.
31 §20 Type F requires dimension metadata that does not exist for this provider.

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


def create_embeddings(config: NoteGPTConfig, request: Dict[str, Any]) -> Dict[str, Any]:
    """NOT IMPLEMENTED — returns the normalized unsupported_capability error."""
    return {"error": err.unsupported_capability("create_embeddings").to_dict()}
