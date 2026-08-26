# -*- coding: utf-8 -*-
"""Configuration for the disabled Arena.ai provider template.

Only an opaque credential reference is accepted. The template never reads,
stores, prints, or transmits a credential value.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional

CREDENTIAL_REF_ENV = "ARENA_CREDENTIAL_REF"
ENDPOINT_ENV = "ARENA_PROVIDER_ENDPOINT"


@dataclass(frozen=True)
class ArenaConfig:
    """Non-secret configuration used for contract inspection only."""

    credential_ref: Optional[str] = None
    endpoint: Optional[str] = None

    @classmethod
    def from_environment(cls) -> "ArenaConfig":
        return cls(
            credential_ref=os.getenv(CREDENTIAL_REF_ENV) or None,
            endpoint=os.getenv(ENDPOINT_ENV) or None,
        )

    @property
    def has_credential_ref(self) -> bool:
        return bool(self.credential_ref)

    def redacted(self) -> Dict[str, object]:
        """Return a log-safe view; never include the reference value itself."""
        return {
            "has_credential_ref": self.has_credential_ref,
            "has_endpoint": bool(self.endpoint),
        }

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return f"ArenaConfig({self.redacted()})"

    __str__ = __repr__
