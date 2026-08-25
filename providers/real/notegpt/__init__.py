# -*- coding: utf-8 -*-
"""
NoteGPT Provider Package.

SPEC : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §6.2 (mature layout)
SHAPE: Session/Cookie Website Provider (31 §20 Type C)
     + Provider-Native Agent Provider  (31 §20 Type L)

STATUS: disabled — 31 §19.13 "Keep provider disabled until tests pass."

The Core imports ONLY `provider.NoteGPTProvider` (30 §2: "Core must not import
provider internals"). Everything else in this package is provider-internal.
"""

from .provider import NoteGPTProvider, get_provider

__all__ = ["NoteGPTProvider", "get_provider"]
__provider_id__ = "notegpt"
__version__ = "1.0.0"
__status__ = "disabled"
