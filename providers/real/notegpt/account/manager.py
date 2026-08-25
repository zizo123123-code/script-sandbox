# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Account — Manager  [STUB — NOT IMPLEMENTED]
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §6.2, §10
POLICY : 01_31_PROVIDER_SCAFFOLDING_AND_ONBOARDING.md §12
SOURCE : inventory/notegpt/CORRECTIONS.md §7  (the key correction)

WHY THIS MODULE IS A STUB
-------------------------
The original limits.md and provider_summary.md both stated that on error 164019
the engine "pulls the next account from accounts_notegpt.json".

CORRECTIONS.md §7 disproved this:
    * accounts_notegpt.json DOES NOT EXIST in the repo
      (`grep -c accounts_notegpt 01.05` = 0)
    * the code calls rotate_identity(), which rotates IP + cookies on the
      SAME account and preserves conversation_id

Verdict: "Account Pool Rotation = NOT_IMPLEMENTED — was claimed as existing."

30 §10.1 states an account pool is OPTIONAL. manifest.yaml declares
account_pool.supported = false, so per 30 §5 this module must not be
implemented. Building it would fake a capability the provider does not have.

WHAT EXISTS INSTEAD
-------------------
Single-account lifecycle:
    runtime/auth.py     — login / re-login on 164003
    runtime/session.py  — rotate_identity(keep_conversation=True)

FUTURE: a real pool is planned as task T-V02-001 item 3. Implement here and
flip account_pool.supported in the manifest at that point.
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict

from .. import errors as err

SUPPORTED = False
REASON = "not_implemented_upstream"

# 30 §10.2 — normalized states, kept here for the future implementation.
PENDING = "PENDING"
READY = "READY"
IN_USE = "IN_USE"
COOLDOWN = "COOLDOWN"
REFRESH_REQUIRED = "REFRESH_REQUIRED"
AUTH_EXPIRED = "AUTH_EXPIRED"
RATE_LIMITED = "RATE_LIMITED"
VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
INVALID = "INVALID"
DISABLED = "DISABLED"


def get_account(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """NOT IMPLEMENTED — no account pool exists for this provider."""
    return {"error": err.unsupported_capability("account_pool").to_dict()}


def list_accounts(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """NOT IMPLEMENTED — see module docstring."""
    return {"error": err.unsupported_capability("account_pool").to_dict()}
