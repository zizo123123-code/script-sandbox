# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Provider — Adapter (the Core's only entry point)
================================================================================
SPEC : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §8.1, §8.2, §15.2

Implements ProviderAdapter:
    getManifest · validateCredential · discoverModels · getCapabilities
    generate · healthCheck · normalizeError

30 §8.1: `generate` is the normalized entry point that dispatches to the
capability-specific operations of §5. An operation that is not declared in
manifest.yaml is rejected with `unsupported_capability` — it is never faked.

30 §17 / 31 §4: this provider is `status: disabled`. Real network calls are
gated behind `_require_enabled()` so that importing or inspecting the provider
can never accidentally execute a live request.
================================================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from . import errors as err
from .config import NoteGPTConfig
from .discovery import capabilities as caps_mod
from .discovery import limits as limits_mod
from .discovery import models as models_mod
from .operations import provider_agent, text_generation
from .provider_health import monitor as health_monitor

MANIFEST_PATH = Path(__file__).resolve().parent / "manifest.yaml"

# Operations this provider declares (manifest.yaml `operations`).
DECLARED_OPERATIONS = frozenset({
    "generate_text",
    "run_provider_agent",
    "analyze_vision",
    "upload_asset",
    "download_asset",
})

UNSUPPORTED_OPERATIONS = frozenset({
    "generate_image",
    "transcribe_audio",
    "synthesize_speech",
    "create_embeddings",
    "rerank_documents",
    "moderate_content",
})


class ProviderDisabledError(RuntimeError):
    """Raised when a live operation is attempted while status != active."""


class NoteGPTProvider:
    """NoteGPT adapter. Session/cookie provider with a native code agent."""

    provider_id = "notegpt"
    provider_name = "NoteGPT"

    def __init__(self, config: Optional[NoteGPTConfig] = None) -> None:
        self.config = config or NoteGPTConfig()
        self._manifest: Optional[Dict[str, Any]] = None

    # =========================================================================
    # 30 §8.1 — Required interface
    # =========================================================================
    def get_manifest(self) -> Dict[str, Any]:
        """Parsed manifest.yaml. Falls back to a minimal dict without PyYAML."""
        if self._manifest is not None:
            return self._manifest
        try:
            import yaml  # optional dependency
            with MANIFEST_PATH.open("r", encoding="utf-8") as fh:
                self._manifest = yaml.safe_load(fh)
        except Exception:
            self._manifest = {
                "id": self.provider_id,
                "name": self.provider_name,
                "status": "disabled",
                "is_template": False,
                "is_functional": False,
                "_manifest_parse": "unavailable_without_pyyaml",
            }
        return self._manifest

    def get_capabilities(self) -> Dict[str, Any]:
        """Declared capabilities — 30 §4.1."""
        return caps_mod.get_capabilities()

    def discover_models(self, account: Any = None) -> List[Dict[str, Any]]:
        """
        Static discovery from the verified 36-model catalog.
        CORRECTIONS.md §6 — phantom models are filtered out by models_mod.
        """
        return models_mod.discover_models()

    def get_limits(self) -> Dict[str, Any]:
        """Normalized rate-limit view — 30 §12."""
        return limits_mod.get_limits()

    def validate_credential(self, credential_ref: Optional[str] = None) -> Dict[str, Any]:
        """
        Credential health. Live probe requires an enabled provider; otherwise
        reports only whether credentials are *present* (never their values).
        """
        if not self.config.has_credentials:
            return {
                "valid": False,
                "state": "INVALID",
                "reason": "no_credentials_configured",
                "checked_live": False,
            }
        if not self._is_enabled():
            return {
                "valid": False,
                "state": "PENDING",
                "reason": "provider_disabled_live_check_skipped",
                "checked_live": False,
            }
        return health_monitor.check_credential(self.config)

    def health_check(self, scope: str = "provider") -> Dict[str, Any]:
        """
        30 §11 — provider health is separate from account health.
        Uses the app-code probes from CORRECTIONS.md §8, not HTTP status.
        """
        if not self._is_enabled():
            return {
                "state": "SUSPENDED",
                "reason": "provider_disabled",
                "scope": scope,
                "checked_live": False,
            }
        return health_monitor.health_check(self.config, scope=scope)

    def normalize_error(self, error: Any = None, **kwargs: Any) -> Dict[str, Any]:
        """30 §14 — normalized error envelope."""
        return err.normalize_error(error, **kwargs).to_dict()

    # =========================================================================
    # 30 §5 + §8.1 — normalized generate, dispatching to capability operations
    # =========================================================================
    def generate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch by requested operation. Undeclared operations are rejected
        with `unsupported_capability` — never silently approximated.
        """
        operation = request.get("operation", "generate_text")

        if operation in UNSUPPORTED_OPERATIONS:
            return {"error": err.unsupported_capability(operation).to_dict()}
        if operation not in DECLARED_OPERATIONS:
            return {"error": err.unsupported_capability(operation).to_dict()}

        self._require_enabled(operation)

        if operation == "generate_text":
            return text_generation.generate_text(self.config, request)
        if operation == "run_provider_agent":
            return provider_agent.run_provider_agent(self.config, request)
        if operation == "analyze_vision":
            # Vision is not a separate endpoint: the sandbox exposes the
            # `image_recognition` tool, so vision runs through the agent path.
            return provider_agent.run_provider_agent(self.config, request)
        if operation in {"upload_asset", "download_asset"}:
            from .assets import download as download_mod
            from .assets import upload as upload_mod
            if operation == "upload_asset":
                return upload_mod.upload_asset(self.config, request)
            return download_mod.download_asset(self.config, request)

        return {"error": err.unsupported_capability(operation).to_dict()}

    # =========================================================================
    # 30 §15.2 — Provider agent interface
    # =========================================================================
    def run_agent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        self._require_enabled("run_provider_agent")
        return provider_agent.run_provider_agent(self.config, request)

    def stream_agent_run(self, request: Dict[str, Any]):
        self._require_enabled("stream_agent_run")
        return provider_agent.stream_agent_run(self.config, request)

    # NOT SUPPORTED — NoteGPT has no run-handle API.
    # State is the conversation_id itself; there is no endpoint to fetch or
    # cancel a run by id. Declaring these would fake functionality (30 §17).
    def create_agent_run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return {"error": err.unsupported_capability("create_agent_run").to_dict()}

    def get_agent_run(self, run_id: str) -> Dict[str, Any]:
        return {"error": err.unsupported_capability("get_agent_run").to_dict()}

    def cancel_agent_run(self, run_id: str) -> Dict[str, Any]:
        return {"error": err.unsupported_capability("cancel_agent_run").to_dict()}

    # =========================================================================
    # Activation gate — 30 §17, 31 §22
    # =========================================================================
    def _is_enabled(self) -> bool:
        m = self.get_manifest()
        return m.get("status") == "active" and m.get("is_functional") is True

    def _require_enabled(self, operation: str) -> None:
        if not self._is_enabled():
            raise ProviderDisabledError(
                f"NoteGPT is status='{self.get_manifest().get('status')}'; "
                f"operation '{operation}' blocked. Enable only after contract "
                f"tests pass and security review completes (31 §22)."
            )


def get_provider(config: Optional[NoteGPTConfig] = None) -> NoteGPTProvider:
    """Factory used by the provider registry."""
    return NoteGPTProvider(config=config)
