# -*- coding: utf-8 -*-
"""Provider-neutral errors for the disabled Arena.ai template."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

PROVIDER_DISABLED = "provider_disabled"
UNSUPPORTED_CAPABILITY = "unsupported_capability"
MISSING_CONFIGURATION = "missing_configuration"
UNKNOWN_ERROR = "unknown_error"

ALL_CATEGORIES = frozenset(
    {
        PROVIDER_DISABLED,
        UNSUPPORTED_CAPABILITY,
        MISSING_CONFIGURATION,
        UNKNOWN_ERROR,
    }
)


@dataclass(frozen=True)
class NormalizedProviderError:
    category: str
    message: str
    retryable: bool = False
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "message": self.message,
            "retryable": self.retryable,
            "details": dict(self.details or {}),
        }


def normalize_error(error: Any = None, *, category: Optional[str] = None) -> NormalizedProviderError:
    """Normalize template failures without exposing input or credentials."""
    if isinstance(error, NormalizedProviderError):
        return error

    chosen = category
    if chosen not in ALL_CATEGORIES:
        chosen = getattr(error, "category", None)
    if chosen not in ALL_CATEGORIES:
        chosen = PROVIDER_DISABLED

    if chosen == PROVIDER_DISABLED:
        message = "Arena.ai provider template is disabled and cannot execute requests."
        details = {"status": "template_disabled", "is_functional": False}
    elif chosen == UNSUPPORTED_CAPABILITY:
        message = "The requested capability is not implemented by this template."
        details = {"status": "template_disabled"}
    elif chosen == MISSING_CONFIGURATION:
        message = "Arena.ai provider configuration is not available."
        details = {"status": "template_disabled"}
    else:
        message = "The Arena.ai provider template returned an unknown error."
        details = {"status": "template_disabled"}

    return NormalizedProviderError(category=chosen, message=message, details=details)
