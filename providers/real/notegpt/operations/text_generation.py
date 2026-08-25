# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Operation — Text Generation
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §5 (generate_text)
SOURCE : projects/ngpt/scripts/01.06 :739-810 (ask_agent_stream)

DECLARED: capabilities.chat / text_generation / streaming = CONFIRMED

Note on shape: NoteGPT has no non-agent text endpoint in any HAR entry —
`chat_mode: "agent"` is always sent (01.06:752). So text generation is the
same transport as the agent, consumed for its text output only. That is why
this module delegates the stream to provider_agent rather than duplicating it.
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .. import errors as err
from ..config import NoteGPTConfig
from ..discovery import models as models_mod
from ..runtime import parser as parser_mod


def generate_text(config: NoteGPTConfig, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalized text generation.

    Returns either {"result": ...} or {"error": <normalized>}.
    Never raises for provider-side failures — 30 §14 requires the Core to make
    decisions from normalized errors only.
    """
    prompt = request.get("prompt") or request.get("message")
    if not prompt:
        return {
            "error": err.ProviderError(
                category=err.BAD_REQUEST,
                retryable=False,
                provider_code="missing_prompt",
                safe_message="A prompt/message is required.",
            ).to_dict()
        }

    resolution = models_mod.resolve_model(request.get("model"))
    if not resolution["resolved"]:
        return {
            "error": err.ProviderError(
                category=err.MODEL_UNAVAILABLE,
                retryable=False,
                provider_code=resolution["reason"],
                safe_message=resolution.get("detail", "Model unavailable."),
            ).to_dict()
        }

    from . import provider_agent

    agent_request = dict(request)
    agent_request["prompt"] = prompt
    agent_request["model"] = resolution["model_id"]

    outcome = provider_agent.run_provider_agent(config, agent_request)
    if "error" in outcome:
        return outcome

    result = outcome.get("result", {})
    return {
        "result": {
            "text": result.get("text", ""),
            "reasoning": result.get("reasoning", ""),
            "model": resolution["model_id"],
            "conversation_id": result.get("conversation_id"),
            "credits_used": result.get("credits_used", 0),
            "finish_reason": result.get("finish_reason"),
        }
    }


def stream_text(config: NoteGPTConfig, request: Dict[str, Any]):
    """
    Streaming variant. Yields only text/reasoning deltas; tool and sandbox
    events are filtered out for callers that want plain text.
    """
    from . import provider_agent

    for event in provider_agent.stream_agent_run(config, request):
        if event.get("type") in {parser_mod.EVENT_TEXT, parser_mod.EVENT_REASONING}:
            yield event
        elif event.get("type") == parser_mod.EVENT_DONE:
            yield event
            return
        elif event.get("type") == parser_mod.EVENT_ERROR:
            yield event
            return
