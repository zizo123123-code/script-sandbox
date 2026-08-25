# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Discovery — Model Bindings
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §6.2, §8.1
SOURCE : projects/ngpt/notegpt_catalog.json — 36 entries, all "200 OK"
         inventory/notegpt/CORRECTIONS.md §6 · CORRECTIONS_ROUND2.md §5

ACCURACY HISTORY (ROUND2 §5)
----------------------------
The original inventory/notegpt/models.md claimed 19 models:
    7 were invented (do not exist), 12 were real, 24 real models were missing.
    Effective accuracy: 12/36 = 33%.

This module therefore reads the CATALOG FILE as its source of truth and
refuses to serve any model not present in it. Phantom models are listed
explicitly so a stale config referencing one fails loudly.

MODALITY WARNING (ROUND2 §5)
----------------------------
The catalog's real fields are: model · status · dur · think · text
There is NO vision/multimodal field. Every "✅ Vision" in the old models.md
was a guess. Accordingly `modality` is reported as "unknown" for every model —
except the two with think=true, where reasoning is genuinely evidenced.
================================================================================
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Catalog location, relative to the repository root.
_CATALOG_CANDIDATES = [
    Path(__file__).resolve().parents[4] / "projects" / "ngpt" / "notegpt_catalog.json",
    Path(__file__).resolve().parents[3] / "projects" / "ngpt" / "notegpt_catalog.json",
]

DEFAULT_MODEL = "deepseek-v4-flash"     # 01.06:100

# CORRECTIONS.md §6 — models invented by the original models.md.
PHANTOM_MODELS = frozenset({
    "claude-3-7-sonnet",
    "claude-3-5-haiku",
    "gemini-2.0-flash",
    "gemini-2.0-pro-exp-02-05",
    "qwen-2.5-max",
    "qwen-2.5-coder-32b-instruct",
    "minimax-01",
})

# Only these two carry think=true in the catalog.
REASONING_MODELS = frozenset({
    "deepseek-reasoner",
    "TA/deepseek-ai/DeepSeek-R1",
})

_cache: Optional[List[Dict[str, Any]]] = None


def _catalog_path() -> Optional[Path]:
    for candidate in _CATALOG_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


def load_catalog(force: bool = False) -> List[Dict[str, Any]]:
    """Load the verified catalog. Returns [] when unavailable (never invents)."""
    global _cache
    if _cache is not None and not force:
        return _cache

    path = _catalog_path()
    if path is None:
        _cache = []
        return _cache

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        _cache = data if isinstance(data, list) else []
    except Exception:
        _cache = []
    return _cache


def discover_models() -> List[Dict[str, Any]]:
    """
    Normalized ModelBinding list — 30 §8.1 discoverModels().

    Static discovery: NoteGPT exposes no model-list endpoint in any HAR entry,
    so bindings come from the measured catalog.
    """
    bindings: List[Dict[str, Any]] = []
    for entry in load_catalog():
        model_id = entry.get("model")
        if not model_id or model_id in PHANTOM_MODELS:
            continue

        is_reasoning = bool(entry.get("think"))
        bindings.append({
            "model_id": model_id,
            "provider": "notegpt",
            "status": entry.get("status", "unknown"),
            "capabilities": {
                "text_generation": True,
                "streaming": True,
                "reasoning": is_reasoning,
                # ROUND2 §5 — no modality evidence exists in the catalog.
                "vision_input": "unknown",
                "image_generation": "unknown",
                "audio_input": "unknown",
            },
            "metrics": {
                "measured_latency_seconds": entry.get("dur"),
                "measurement_source": "notegpt_catalog.json",
            },
            "context_window": "unknown",     # CORRECTIONS.md §7
            "is_default": model_id == DEFAULT_MODEL,
        })
    return bindings


def list_model_ids() -> List[str]:
    return [b["model_id"] for b in discover_models()]


def is_valid_model(model_id: str) -> bool:
    """A model is valid only if the catalog measured it as reachable."""
    return model_id in set(list_model_ids())


def is_phantom_model(model_id: str) -> bool:
    """True for the 7 models the original documentation invented."""
    return model_id in PHANTOM_MODELS


def get_reasoning_models() -> List[str]:
    return sorted(REASONING_MODELS)


def resolve_model(requested: Optional[str] = None) -> Dict[str, Any]:
    """
    Resolve a requested model id.

    Phantom models are rejected with an explicit reason rather than being
    silently swapped for the default — a silent swap would hide the fact that
    a caller is relying on documentation that was wrong.
    """
    if not requested:
        return {"model_id": DEFAULT_MODEL, "resolved": True, "reason": "default"}
    if is_phantom_model(requested):
        return {
            "model_id": None,
            "resolved": False,
            "reason": "phantom_model",
            "detail": (
                f"'{requested}' does not exist on NoteGPT; it was invented by "
                f"inventory/notegpt/models.md (see CORRECTIONS.md §6)."
            ),
        }
    if not is_valid_model(requested):
        return {
            "model_id": None,
            "resolved": False,
            "reason": "unknown_model",
            "detail": f"'{requested}' is not present in notegpt_catalog.json.",
        }
    return {"model_id": requested, "resolved": True, "reason": "catalog_match"}
