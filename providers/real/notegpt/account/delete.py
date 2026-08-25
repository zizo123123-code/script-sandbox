# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Account — Delete  [STUB — NOT APPLICABLE]
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §6.2 (account/)
POLICY : 01_31_PROVIDER_SCAFFOLDING_AND_ONBOARDING.md §12

NOT_APPLICABLE — no account-management API exists.

NoteGPT exposes no endpoint to delete an account programmatically; none appears
in any of the 916 observed HAR entries. Account administration happens through
the website UI by a human operator.

Since manifest.yaml declares account_pool.supported = false, there is also no
platform-side pool record for this operation to act upon. The file exists to
keep the §6.2 structure complete.
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict

from .. import errors as err

SUPPORTED = False
REASON = "no_provider_api"


def delete_account(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """NOT APPLICABLE — see module docstring."""
    return {"error": err.unsupported_capability("delete_account").to_dict()}
