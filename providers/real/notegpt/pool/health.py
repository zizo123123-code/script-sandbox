# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Pool — Health  [STUB — NOT APPLICABLE]
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §6.2, §10.1, §10.4
POLICY : 01_31_PROVIDER_SCAFFOLDING_AND_ONBOARDING.md §12
SOURCE : inventory/notegpt/CORRECTIONS.md §7

NOT_APPLICABLE — this provider has no account pool.

30 §10.1: "Account Pool Is Optional". manifest.yaml declares
    account_pool.supported: false
    account_pool.lease_required: false

CORRECTIONS.md §7 established why: the pool that limits.md and
provider_summary.md described does not exist. accounts_notegpt.json is absent
from the repo, and the recovery path in the reference code is rotate_identity()
— IP + cookie rotation on a SINGLE account, preserving conversation_id.

30 §10.4 requires leases only "If a provider uses account pools". With one
account and no pool there is nothing to select, lease, or cool down, so
implementing this module would create machinery with no referent.

The file exists to keep the §6.2 structure complete. If an account pool is
built later (planned as T-V02-001 item 3), implement here and flip
account_pool.supported in the manifest — the Core reads capabilities, so no
Core change is needed.
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict

from .. import errors as err

SUPPORTED = False
REASON = "account_pool_not_supported"


def pool_health(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """NOT APPLICABLE — no account pool for this provider."""
    return {"error": err.unsupported_capability("pool_health").to_dict()}
