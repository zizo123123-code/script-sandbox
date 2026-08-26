# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT — Repo Hygiene Guards (P1 secrets ignore · P2 fabricated upload URL)
================================================================================
SPEC : 01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md §2, §18.3 · 31 §19.5

WHY THESE EXIST
---------------
Both defects guarded here were fixed as CONFIGURATION / REFERENCE-SCRIPT edits,
not as provider-package logic. That makes them exactly the kind of fix that
regresses silently: nothing imports `.gitignore`, and nothing imports the
reference script, so the whole 107-test suite stays green while either one is
quietly undone.

P1 — .gitignore had no secret patterns at all
    Verified before the fix, every one of these came back "WOULD BE COMMITTED":
        active_token.txt · .env · .env.local · token.txt · secrets.json
        · credentials.json
    A single `git add -A` would have committed a live session token. This is
    also the documented reason the reference implementation's `active_token.txt`
    was rejected instead of adopted.

P2 — the reference script fabricated an upload URL on failure (01.06:174)
        https://cdn.ng-resource.com/product/upload/notegpt/ai-chat/2026/08/25/<name>
    Three defects, the third being the dangerous one:
      1. the date is hardcoded, so the path is structurally dead on any other day
      2. the file was never uploaded there — live curl at fix time returned 404
      3. it returns a truthy str, so all four consumers gated on
         `if s.uploaded_url:` read a FAILED upload as a SUCCESS
    Merely updating the date would leave (2) and (3) intact, so the fix was to
    return None honestly.

These tests assert the repo state itself, so undoing either fix fails here.

Run: python3 -m pytest providers/real/notegpt/tests/test_repo_hygiene.py -v
================================================================================
"""

from __future__ import annotations

import ast
import pathlib
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
REFERENCE_SCRIPT = REPO_ROOT / "projects" / "ngpt" / "scripts" / "01.06_notegpt_agent_mode.py"


# ==============================================================================
# P1 — secret files must not be committable
# ==============================================================================
# Filenames that must be ignored. `git check-ignore` is the authority here
# rather than reading .gitignore as text, because only git implements the real
# precedence and negation rules.
SECRET_PATHS = [
    "active_token.txt",
    "providers/real/notegpt/active_token.txt",
    "token.txt",
    "session_token.txt",
    ".env",
    ".env.local",
    ".env.production",
    "secrets.json",
    "app_secrets.json",
    "credentials.json",
    "server.pem",
    "private.key",
    "id_rsa",
    "accounts_notegpt.json",
    "cookies.json",
]

# The negation side. Over-broad patterns are their own failure mode: ignoring
# tracked tooling or the env TEMPLATE would be a regression, not a fix.
MUST_STAY_TRACKED = [
    ".connect/tools/secret_scan.py",
    ".env.example",
    ".env.template",
    ".env.sample",
    "providers/real/notegpt/config.py",
    "providers/real/notegpt/tests/mock_transport.py",
]


def _is_ignored(rel_path: str) -> bool:
    """True if git would ignore `rel_path`."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", "--no-index", rel_path],
        cwd=REPO_ROOT,
        capture_output=True,
    )
    # 0 = ignored, 1 = not ignored, other = error
    assert result.returncode in (0, 1), (
        f"git check-ignore failed for {rel_path}: {result.stderr.decode()}"
    )
    return result.returncode == 0


@pytest.mark.parametrize("secret_path", SECRET_PATHS)
def test_secret_files_are_ignored(secret_path):
    """A secret-bearing filename must never be committable."""
    assert _is_ignored(secret_path), (
        f"{secret_path!r} is NOT ignored — `git add -A` would commit a secret"
    )


@pytest.mark.parametrize("tracked_path", MUST_STAY_TRACKED)
def test_tracked_files_are_not_swallowed_by_secret_patterns(tracked_path):
    """The ignore patterns must not be so broad they hide real files."""
    assert not _is_ignored(tracked_path), (
        f"{tracked_path!r} became ignored — the secret patterns are too broad"
    )


def test_no_currently_tracked_file_became_ignored():
    """
    A safety net for the whole repo: adding ignore rules must not orphan any
    file that is already tracked.
    """
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True
    ).stdout.split("\n")
    tracked = [t for t in tracked if t.strip()]
    assert tracked, "git ls-files returned nothing — cannot verify"

    check = subprocess.run(
        ["git", "check-ignore", "--stdin"],
        cwd=REPO_ROOT,
        input="\n".join(tracked),
        capture_output=True,
        text=True,
    )
    orphaned = [line for line in check.stdout.split("\n") if line.strip()]
    assert not orphaned, f"tracked files are now ignored: {orphaned}"


# ==============================================================================
# P2 — the reference script must not fabricate an upload URL
# ==============================================================================
def _reference_ast():
    if not REFERENCE_SCRIPT.exists():
        pytest.skip(f"reference script not present: {REFERENCE_SCRIPT}")
    source = REFERENCE_SCRIPT.read_text(encoding="utf-8")
    return source, ast.parse(source)


def _upload_url_func(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "get_public_url_for_file":
            return node
    pytest.fail("get_public_url_for_file() not found in the reference script")


def test_upload_helper_returns_none_on_failure_not_a_fabricated_url():
    """
    Every failure path must return None. A str on failure is indistinguishable
    from success to the four `if s.uploaded_url:` consumers.
    """
    _, tree = _reference_ast()
    func = _upload_url_func(tree)

    returns = [n for n in ast.walk(func) if isinstance(n, ast.Return)]
    assert returns, "function has no return statements"

    none_returns = [
        n for n in returns
        if n.value is None
        or (isinstance(n.value, ast.Constant) and n.value.value is None)
    ]
    assert none_returns, (
        "no failure path returns None — a failed upload still looks successful"
    )


def test_upload_helper_declares_an_optional_return_type():
    """The signature must admit failure, so callers are forced to handle it."""
    _, tree = _reference_ast()
    func = _upload_url_func(tree)

    assert func.returns is not None, "return annotation missing"
    annotation = ast.unparse(func.returns)
    assert "Optional" in annotation or "None" in annotation, (
        f"return type {annotation!r} claims a URL is always produced"
    )


def test_no_fabricated_cdn_url_in_executable_code():
    """
    The hardcoded-date CDN URL must not exist as EXECUTABLE code.

    Docstrings are excluded on purpose: the fix documents the removed URL to
    explain the defect, and that prose must not be mistaken for the bug. The
    line-978 regex is also legitimate — it EXTRACTS real cdn.ng-resource.com
    links out of provider replies, it does not manufacture one.
    """
    source, tree = _reference_ast()
    func = _upload_url_func(tree)

    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                docstrings.add(doc)

    offenders = []
    for node in ast.walk(func):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in docstrings:
                continue
            if "ng-resource" in node.value or "2026/08/25" in node.value:
                offenders.append((node.lineno, node.value[:80]))
        if isinstance(node, ast.JoinedStr):
            raw = ast.get_source_segment(source, node) or ""
            if "ng-resource" in raw or "2026/08/25" in raw:
                offenders.append((node.lineno, raw[:80]))

    assert not offenders, f"fabricated CDN URL still built in code: {offenders}"


def test_upload_failure_is_not_silently_swallowed():
    """
    The original handler was a bare `except Exception: pass`, which hid the
    cause and then fell through to the fabricated URL. A failure must be
    reported, not swallowed.
    """
    _, tree = _reference_ast()
    func = _upload_url_func(tree)

    for handler in [n for n in ast.walk(func) if isinstance(n, ast.ExceptHandler)]:
        body_is_only_pass = all(isinstance(stmt, ast.Pass) for stmt in handler.body)
        assert not body_is_only_pass, (
            "upload failure is swallowed by `except: pass` — the caller cannot tell"
        )
