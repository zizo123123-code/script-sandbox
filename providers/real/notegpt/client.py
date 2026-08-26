# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT — Client Facade
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §6.2 (client.*)
SOURCE : projects/ngpt/scripts/01.06 :459-911 (NoteGPTAgentClient)

A thin, stateful convenience wrapper that binds one NoteGPTConfig to one
ConversationSession, so a caller does not have to thread session state through
every call. All protocol work lives in runtime/ and operations/ — this file
only holds the pairing.

The Core does NOT use this class; it uses provider.NoteGPTProvider (§8.1).
This facade exists for provider-internal tooling and tests.
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict, Generator, List, Optional

from .config import NoteGPTConfig
from .discovery import models as models_mod
from .operations import provider_agent, text_generation
from .provider_health import monitor as monitor_mod
from .runtime import auth as auth_mod
from .runtime import request as request_mod
from .runtime import session as session_mod


class NoteGPTClient:
    """Stateful client bound to a single conversation/sandbox session."""

    def __init__(
        self,
        config: Optional[NoteGPTConfig] = None,
        *,
        model: Optional[str] = None,
        is_auto_model: bool = False,
        conversation_id: Optional[str] = None,
    ) -> None:
        self.config = config or NoteGPTConfig()
        if model:
            self.config.model = model

        self.session = (
            session_mod.resume_session(conversation_id, model=model, is_auto_model=is_auto_model)
            if conversation_id
            else session_mod.new_session(model=model, is_auto_model=is_auto_model)
        )
        self._scraper: Optional[Any] = None

    # --- lazy transport ------------------------------------------------------
    @property
    def scraper(self) -> Any:
        if self._scraper is None:
            self._scraper = request_mod.create_scraper()
        return self._scraper

    # --- auth ----------------------------------------------------------------
    def login(self) -> Dict[str, Any]:
        token, error = auth_mod.login(self.config, scraper=self.scraper)
        if error:
            return {"ok": False, "error": error}
        return {"ok": True, "has_token": bool(token)}

    # --- generation ----------------------------------------------------------
    def ask(self, prompt: str, files: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Blocking agent run on the current conversation."""
        return provider_agent.run_provider_agent(
            self.config,
            {
                "prompt": prompt,
                "files": files,
                "session": self.session,
                "scraper": self.scraper,
                "model": self.session.model,
                "is_auto_model": self.session.is_auto_model,
            },
        )

    def stream(self, prompt: str, files: Optional[List[Any]] = None) -> Generator[Dict[str, Any], None, None]:
        """Streaming agent run yielding normalized events."""
        return provider_agent.stream_agent_run(
            self.config,
            {
                "prompt": prompt,
                "files": files,
                "session": self.session,
                "scraper": self.scraper,
                "model": self.session.model,
                "is_auto_model": self.session.is_auto_model,
            },
        )

    def generate_text(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        return text_generation.generate_text(
            self.config,
            {
                "prompt": prompt,
                "model": model or self.session.model,
                "session": self.session,
                "scraper": self.scraper,
            },
        )

    # --- session -------------------------------------------------------------
    def new_conversation(self) -> str:
        """Start fresh — discards the current sandbox session."""
        return self.session.new_conversation()

    def rotate_identity(self, keep_conversation: bool = True) -> None:
        """Rotate IP/cookies. Default keeps the sandbox alive (lesson #137)."""
        self.session.rotate_identity(keep_conversation=keep_conversation)
        self._scraper = None      # force a fresh TLS fingerprint

    @property
    def conversation_id(self) -> str:
        return self.session.conversation_id

    def telemetry(self) -> Dict[str, Any]:
        return self.session.to_dict()

    # --- discovery / health --------------------------------------------------
    def list_models(self) -> List[str]:
        return models_mod.list_model_ids()

    def health(self) -> Dict[str, Any]:
        return monitor_mod.health_check(self.config)

    def fetch_shared_agents(self) -> Dict[str, Any]:
        """
        GET /api/v1/agent/share/list — HAR x16.
        Missing from the original agent.md; added by CORRECTIONS.md §2.
        """
        from . import errors as err

        try:
            response = self.scraper.get(
                f"{self.config.url('agent_share_list')}?page_no=1&page_size=50&language=en",
                timeout=10,
            )
        except Exception as exc:
            return {"error": err.normalize_error(exc).to_dict()}

        try:
            body = response.json()
        except Exception:
            return {"error": err.normalize_error(http_status=response.status_code).to_dict()}

        if not err.is_success_code(body.get("code")):
            return {"error": err.normalize_error(http_status=response.status_code, body=body).to_dict()}

        return {"result": (body.get("data") or {}).get("list", [])}


if __name__ == "__main__":
    from .__main__ import main
    main()
