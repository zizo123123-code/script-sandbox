# -*- coding: utf-8 -*-
"""Arena.ai provider adapter — deliberately disabled template.

This module implements the normalized inspection surface from provider spec
§8.1. It contains no HTTP client and has no live execution path. A provider
adapter can be added only after Arena.ai publishes or the owner supplies a
verified API/auth contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from . import errors as err
from .config import ArenaConfig
from .discovery import capabilities as caps_mod
from .discovery import models as models_mod
from .provider_health import monitor as health_monitor

MANIFEST_PATH = Path(__file__).resolve().parent / "manifest.yaml"

# The operation is recorded in the template to preserve the Type L shape, but
# the activation state below makes it non-routable and non-executable.
DECLARED_OPERATIONS = frozenset({"run_provider_agent"})

_DEFAULT_MANIFEST: Dict[str, Any] = {
    "id": "arena",
    "name": "Arena.ai Agent Provider",
    "version": "0.1.0",
    "status": "template_disabled",
    "is_template": True,
    "is_functional": False,
    "real_provider_required": True,
    "auth": {"types": [], "supports_refresh": False, "credential_policy": "reference_only"},
    "account_pool": {
        "supported": False,
        "required": False,
        "lease_required": False,
        "fencing_required": False,
        "reason": "not_applicable_until_provider_contract_exists",
    },
    "capabilities": caps_mod.get_capabilities(),
    "operations": {"run_provider_agent": True},
    "authoritative_details": {
        "endpoint": "unknown",
        "authentication": "unknown",
        "model_catalog": "unknown",
        "event_schema": "unknown",
        "rate_limits": "unknown",
    },
    "models": {"discovery": "not_implemented", "static_models": []},
    "agent_module": {
        "supported": True,
        "type": "provider_agent_template",
        "state_model": "unknown",
        "provider_managed_state": "unknown",
        "supports_provider_tools": "unknown",
        "supports_platform_tools": False,
    },
    "security": {
        "provider_side_tools_allowed_by_default": False,
        "requires_capability_firewall": True,
        "requires_evaluation": True,
        "requires_audit": True,
    },
}


class ArenaProvider:
    """Non-routable Arena.ai provider template."""

    provider_id = "arena"
    provider_name = "Arena.ai Agent Provider"
    status = "template_disabled"
    is_functional = False

    def __init__(self, config: Optional[ArenaConfig] = None) -> None:
        self.config = config or ArenaConfig.from_environment()
        self._manifest: Optional[Dict[str, Any]] = None

    def get_manifest(self) -> Dict[str, Any]:
        """Return the YAML manifest, with a dependency-free safe fallback."""
        if self._manifest is not None:
            return self._manifest
        try:
            import yaml  # optional dependency used only for inspection

            with MANIFEST_PATH.open("r", encoding="utf-8") as manifest_file:
                parsed = yaml.safe_load(manifest_file)
            self._manifest = parsed if isinstance(parsed, dict) else dict(_DEFAULT_MANIFEST)
        except Exception:
            self._manifest = dict(_DEFAULT_MANIFEST)
        return self._manifest

    def get_capabilities(self) -> Dict[str, Any]:
        return caps_mod.get_capabilities()

    def discover_models(self, account: Any = None) -> List[Dict[str, Any]]:
        """No model catalog exists until a real Arena contract is supplied."""
        return models_mod.discover_models()

    def validate_credential(self, credential_ref: Optional[str] = None) -> Dict[str, Any]:
        """Inspect presence only; never perform a live validation from a template."""
        present = bool(credential_ref or self.config.credential_ref)
        return {
            "valid": False,
            "state": "PENDING" if present else "INVALID",
            "reason": "template_disabled_live_check_skipped" if present else "no_credential_reference",
            "checked_live": False,
        }

    def get_capabilities_for_routing(self) -> Dict[str, Any]:
        """Return no routable capabilities while this is a template."""
        return {}

    def health_check(self, scope: str = "provider") -> Dict[str, Any]:
        return health_monitor.health_check(scope=scope)

    def normalize_error(self, error: Any = None, **kwargs: Any) -> Dict[str, Any]:
        return err.normalize_error(error, **kwargs).to_dict()

    def generate(self, request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reject every execution attempt; this template never calls a network."""
        return {
            "error": err.normalize_error(category=err.PROVIDER_DISABLED).to_dict(),
            "provider": self.provider_id,
        }

    def is_routable(self) -> bool:
        """Template providers are excluded from router candidates by contract."""
        return False

    def redacted(self) -> Dict[str, object]:
        return {
            "provider_id": self.provider_id,
            "status": self.status,
            "is_functional": self.is_functional,
            "config": self.config.redacted(),
        }


def get_provider(config: Optional[ArenaConfig] = None) -> ArenaProvider:
    return ArenaProvider(config=config)
