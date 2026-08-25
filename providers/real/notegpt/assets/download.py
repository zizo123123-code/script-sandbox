# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Assets — Download
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §8.2 (ProviderAssets)
SOURCE : projects/ngpt/scripts/01.06 :935-1010 (extract_and_save_sandbox_files)
         inventory/notegpt/upload.md §3

The sandbox produces files during an agent run and exposes them as CDN URLs in
the stream output. Download is therefore a plain GET of a URL that appeared in
the response — there is no provider download API.

01.06:950 matches CDN links with the pattern `https://cdn\\.ng-resource\\.com/`.
================================================================================
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .. import errors as err
from ..config import NoteGPTConfig

# 01.06:950
CDN_URL_PATTERN = re.compile(r"https://cdn\.ng-resource\.com/[^\s\)\"']+")

# CORRECTIONS.md §5 — OSS links carry Expires=...; treat all asset URLs as
# short-lived and download promptly rather than storing the URL.
URL_LIFETIME = "short_lived_signed"


def extract_asset_urls(text: str) -> List[str]:
    """Collect CDN asset URLs from streamed reasoning/answer text."""
    if not text:
        return []
    seen: List[str] = []
    for match in CDN_URL_PATTERN.findall(text):
        if match not in seen:
            seen.append(match)
    return seen


def download_asset(config: NoteGPTConfig, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Download one asset by URL.

    Returns the bytes to the caller; it does NOT write to disk. Choosing a
    destination path is the platform's job — a provider writing to the local
    filesystem would escape tenant scoping (30 §15.4).
    """
    url: Optional[str] = request.get("url")
    if not url:
        return {
            "error": err.ProviderError(
                category=err.BAD_REQUEST,
                retryable=False,
                provider_code="no_url_provided",
                safe_message="download_asset requires a url.",
            ).to_dict()
        }

    from ..runtime import request as request_mod

    scraper = request.get("scraper") or request_mod.create_scraper()
    try:
        response = scraper.get(url, timeout=config.timeout)
    except Exception as exc:
        return {"error": err.normalize_error(exc).to_dict()}

    if getattr(response, "status_code", None) != 200:
        return {"error": err.normalize_error(http_status=response.status_code).to_dict()}

    return {
        "result": {
            "url": url,
            "content": response.content,
            "size_bytes": len(response.content),
            "content_type": response.headers.get("Content-Type", "unknown"),
        }
    }
