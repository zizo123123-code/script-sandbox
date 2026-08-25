# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Account — Create  [STUB — NOT IMPLEMENTED]
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §4.2 (account_registration)
POLICY : 01_31 §12 · Security note in 31 §20 Type C
SOURCE : inventory/notegpt/CORRECTIONS_ROUND2.md §0 (registration endpoints seen in HAR)

EVIDENCE
--------
ROUND2 §0 notes the HAR contains:
    POST /api/v1/auth/email/register          x1
    POST /api/v1/auth/email/register/confirm  x2

So registration IS technically reachable. It is deliberately NOT implemented.

WHY NOT
-------
1. 31 §20 Type C security note: "Do not build CAPTCHA bypass or anti-abuse
   circumvention." Automated account creation on a free tier to multiply quota
   is exactly the anti-abuse circumvention that rule targets.
2. Email confirmation requires an inbox round-trip. 31 §20 Type C requires
   representing such states as VERIFICATION_REQUIRED / PENDING_OPERATOR_ACTION,
   not automating them away.
3. manifest.yaml declares account_pool.supported = false, so there is no
   consumer for programmatically created accounts.

Accounts must be provisioned by an operator and supplied via credentials.
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict

from .. import errors as err

SUPPORTED = False
REASON = "anti_abuse_policy"

# 31 §20 Type C — the correct representation for a human-gated step.
VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
PENDING_OPERATOR_ACTION = "PENDING_OPERATOR_ACTION"


def create_account(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """NOT IMPLEMENTED by policy — operator provisioning required."""
    return {
        "error": err.ProviderError(
            category=err.UNSUPPORTED_CAPABILITY,
            retryable=False,
            provider_code="registration_not_automated",
            safe_message=(
                "Automated account creation is not implemented by policy "
                "(31 §20 Type C anti-abuse rule). Provision accounts manually."
            ),
            details={"state": PENDING_OPERATOR_ACTION},
        ).to_dict()
    }
