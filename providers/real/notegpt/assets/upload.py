# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Assets — Upload
================================================================================
SPEC   : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §8.2 (ProviderAssets)
SOURCE : inventory/notegpt/CORRECTIONS.md §5 · CORRECTIONS_ROUND2.md §3

TWO PATHS EXIST, AND THEY DISAGREE — read this before changing anything
----------------------------------------------------------------------

PATH A — the official provider path (documented, NOT implemented)
    POST /api/v1/upload/sign-url   ->   PUT to Alibaba OSS
    Verified present in the HAR (200 OK). BUT `grep -c "sign-url"` in the
    reference scripts returns 0 — the code never uses it.
    BLOCKER: the sign-url request body carries an HMAC `sign` field whose
    derivation is undocumented. CORRECTIONS.md §5 calls it "the single most
    important technical obstacle". It cannot be implemented by guessing.

PATH B — what the reference code actually does (01.06:166)
    POST https://tmpfiles.org/api/v1/upload
    A PUBLIC third-party host. Every attachment transits it before reaching
    NoteGPT, and becomes reachable by public URL.
    ROUND2 §3 flags this as a data-exposure issue.

ALSO BROKEN — the CDN fallback (01.06:174)
    The fallback URL embeds a hardcoded date `2026/08/25`. It is structurally
    dead on any other day, and the file was never uploaded to that host anyway.

DECISION IMPLEMENTED HERE
-------------------------
Path A is stubbed with an explicit blocker (no invented HMAC).
Path B is NOT re-implemented: routing tenant data through a public third-party
host cannot be a provider default under 30 §15.4 (tenant isolation) and
31 §19.10 (security checks). It is available only behind an explicit,
caller-supplied opt-in flag so the risk is a conscious decision, never silent.
================================================================================
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .. import errors as err
from ..config import NoteGPTConfig

# Path A
OFFICIAL_SIGN_URL_ENDPOINT = "/api/v1/upload/sign-url"
OSS_HOST = "nc-product-us-oss.oss-us-west-1.aliyuncs.com"
OSS_URL_TTL_SECONDS = 600          # Expires=... ~10 minutes, NOT permanent
OFFICIAL_PATH_STATUS = "documented_not_implemented"
OFFICIAL_PATH_BLOCKER = "hmac_sign_field_undocumented"

# Path B
THIRD_PARTY_UPLOAD_URL = "https://tmpfiles.org/api/v1/upload"
THIRD_PARTY_STATUS = "implemented_in_reference_script_only"

# CORRECTIONS.md §5 — both were unsourced claims in the original upload.md
MAX_FILE_SIZE = "unknown"          # "50 MB" had no evidence
SUPPORTED_FORMATS = "unknown"      # the code does not restrict formats


def upload_asset(config: NoteGPTConfig, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upload an asset.

    Without `allow_third_party_transit=True` this returns a normalized error
    describing both paths, rather than silently shipping caller data to a
    public host.
    """
    file_ref = request.get("file") or request.get("path")
    if not file_ref:
        return {
            "error": err.ProviderError(
                category=err.BAD_REQUEST,
                retryable=False,
                provider_code="no_file_provided",
                safe_message="upload_asset requires a file reference.",
            ).to_dict()
        }

    if not request.get("allow_third_party_transit"):
        return {
            "error": err.ProviderError(
                category=err.UNSUPPORTED_CAPABILITY,
                retryable=False,
                provider_code="upload_path_unavailable",
                safe_message=(
                    "The official upload path is not implementable (undocumented "
                    "HMAC sign field), and the only working path transits a public "
                    "third-party host. Set allow_third_party_transit=True to opt in "
                    "explicitly."
                ),
                details={
                    "official_path": {
                        "endpoint": OFFICIAL_SIGN_URL_ENDPOINT,
                        "status": OFFICIAL_PATH_STATUS,
                        "blocker": OFFICIAL_PATH_BLOCKER,
                    },
                    "third_party_path": {
                        "host": THIRD_PARTY_UPLOAD_URL,
                        "status": THIRD_PARTY_STATUS,
                        "risk": "public_url_data_exposure",
                    },
                },
            ).to_dict()
        }

    return {
        "error": err.ProviderError(
            category=err.UNSUPPORTED_CAPABILITY,
            retryable=False,
            provider_code="third_party_upload_not_implemented_here",
            safe_message=(
                "Third-party upload transit is acknowledged but deliberately not "
                "implemented in the provider package. Perform the upload in the "
                "caller so the data-exposure decision stays auditable, then pass "
                "the resulting URL via build_native_files_payload()."
            ),
        ).to_dict()
    }


def request_signed_url(config: NoteGPTConfig, filename: str, file_size: int) -> Dict[str, Any]:
    """
    STUB — Path A step 1.

    The request body shape IS known (CORRECTIONS.md §5):
        {"t", "app_id", "filename", "file_size", "headers", "biz", "sign"}
    but `sign` is an HMAC over undisclosed inputs with an unknown key. Any
    implementation would be a guess, so this returns the blocker instead.
    """
    return {
        "error": err.ProviderError(
            category=err.UNSUPPORTED_CAPABILITY,
            retryable=False,
            provider_code=OFFICIAL_PATH_BLOCKER,
            safe_message=(
                "Cannot build the sign-url request: the HMAC 'sign' field "
                "derivation is undocumented."
            ),
            details={
                "known_body_fields": ["t", "app_id", "filename", "file_size", "headers", "biz", "sign"],
                "unknown": "sign (HMAC algorithm + key)",
                "oss_host": OSS_HOST,
                "url_ttl_seconds": OSS_URL_TTL_SECONDS,
            },
        ).to_dict()
    }


# ==============================================================================
# TWO PAYLOAD SHAPES — DO NOT INTERCHANGE (T-03)
# ==============================================================================
# The reference implementation carries attachments in two *different* shapes,
# built by two different functions. Using one where the other belongs sends a
# structurally invalid body that the provider silently ignores.
#
#   stream `files[]`        01.06:273-296  build_stream_files_payload()
#       {file_name, file_size, file_url, file_content, mime_type}
#
#   history `fileInfos[]`   01.06:580-594  build_history_file_infos()
#       {type, url_type, url, title, size, origin_url, transcriptUrl}
#
# NOTE: `build_native_files_payload()` is a DEPRECATED ALIAS of the *history*
# builder despite its name suggesting the stream shape. This comment used to
# map it to stream `files[]`, which is precisely the confusion that made the
# generation body ship raw caller dicts. Do not reintroduce that mapping.
#
# This module owns both schemas; callers must not hand-assemble either.
# ==============================================================================


def _read(src: Any, *names: str, default: Any = None) -> Any:
    """
    Read the first present field from a dict or an object.

    Accepts both the caller-facing spelling (`url`, `name`, `size`) and the
    native spellings (`file_url`, `file_name`, `file_size`) so an attachment
    already in one native shape can still be converted to the other.
    """
    for name in names:
        if isinstance(src, dict):
            if src.get(name) not in (None, ""):
                return src[name]
        else:
            value = getattr(src, name, None)
            if value not in (None, ""):
                return value
    return default


def build_history_file_infos(sources: list) -> list:
    """
    Build the browser-history `fileInfos[]` array — 01.06:580-594.

    Shape (7 fields): type · url_type · url · title · size · origin_url ·
    transcriptUrl, where type 10 = image and 20 = document.

    This is the shape consumed by session pre-registration (/api/v2/ai-chat).
    It is NOT the generation `files[]` shape. Pure assembly: no network I/O.
    """
    file_infos = []
    for src in sources or []:
        url = _read(src, "url", "file_url", "uploaded_url")
        if not url:
            continue
        name = _read(src, "name", "file_name", "title", default="file")
        kind = _read(src, "type", "kind", default="file")
        size = _read(src, "size", "file_size", "file_size_bytes")
        file_infos.append({
            "type": 10 if kind == "image" else 20,
            "url_type": 1,
            "url": url,
            "title": name,
            "size": size or 1024,
            "origin_url": url,
            "transcriptUrl": "",
        })
    return file_infos


def build_stream_files_payload(sources: list) -> list:
    """
    Build the generation `files[]` array — 01.06:273-296 (HAR Entry 19).

    Shape (5 fields): file_name · file_size · file_url · file_content ·
    mime_type. This is the shape the /api/v2/chat/stream body expects, and it
    is deliberately distinct from `build_history_file_infos()`.
    """
    native_files = []
    for src in sources or []:
        url = _read(src, "url", "file_url", "uploaded_url")
        if not url:
            continue
        native_files.append({
            "file_name": _read(src, "name", "file_name", "title", default="file"),
            "file_size": _read(src, "size", "file_size", "file_size_bytes") or 1024,
            "file_url": url,
            "file_content": url,
            "mime_type": _read(src, "mime_type", "mimetype", "content_type"),
        })
    return native_files


def build_native_files_payload(sources: list) -> list:
    """
    DEPRECATED ALIAS — kept so existing callers do not break.

    Despite its name it always produced the *history* `fileInfos[]` shape, not
    the generation `files[]` shape its name implies. That mismatch is exactly
    the confusion the two functions above remove. Prefer calling
    `build_history_file_infos()` or `build_stream_files_payload()` explicitly.
    """
    return build_history_file_infos(sources)
