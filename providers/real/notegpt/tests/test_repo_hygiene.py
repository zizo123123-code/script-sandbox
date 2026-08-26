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
import re
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


# ==============================================================================
# P1b — the repo-wide secret gate must judge VALUES, not NAMES
# ==============================================================================
# `secret_scan.py` is the gate that `doctor.py` does not provide. It is a
# standalone script nothing imports, so a regression in it is invisible to the
# rest of the suite — the same reason the guards above exist.
#
# Two false-positive classes were measured on it, sharing one root: the rules
# match `<sensitive key> = "<value>"` without asking whether the captured value
# is a secret or merely the NAME of the env var the secret is read from.
#     ENV_PASSWORD = "NOTEGPT_PASSWORD"   <- config.py:105, flagged (wrong)
#     PASSWORD     = <a literal secret>   <- flagged (right)
# It reported 32 secrets where 29 were real; the 3 extras were the very
# constants that keep credentials out of the source, plus a comment describing
# that pattern. A gate that cries wolf on the correct pattern trains people to
# ignore it, which is how the 29 real ones survive.
#
# Both directions are asserted here: names stay silent, and every real form
# still fires. The second half is what stops the fix from becoming a blindfold.
def _run_secret_scan(tmp_path, body: str):
    """Run the real gate over a throwaway file inside the repo, return findings."""
    import sys

    sys.path.insert(0, str(REPO_ROOT / ".connect" / "tools"))
    try:
        import secret_scan
    finally:
        sys.path.pop(0)

    probe_dir = REPO_ROOT / ".tmp_hygiene_probe"
    probe_dir.mkdir(exist_ok=True)
    probe = probe_dir / "probe.py"
    try:
        probe.write_text(body, encoding="utf-8")
        return secret_scan.scan_file(probe)
    finally:
        probe.unlink(missing_ok=True)
        probe_dir.rmdir()


def test_secret_scan_does_not_flag_env_var_names():
    """
    An env-var NAME is not a credential. Flagging `ENV_PASSWORD =
    "NOTEGPT_PASSWORD"` punishes the mechanism that keeps secrets out of source.
    """
    findings = _run_secret_scan(
        None,
        'ENV_EMAIL = "NOTEGPT_EMAIL"\n'
        'ENV_PASSWORD = "NOTEGPT_PASSWORD"\n'
        'ENV_SESSION_TOKEN = "NOTEGPT_SESSION_TOKEN"\n',
    )
    assert not findings, f"env var NAMES misreported as secrets: {findings}"


def test_secret_scan_still_flags_every_real_secret_form():
    """
    The name/value exemption must not become a blindfold. Every SPELLING below
    is one that leaked in this repo's history; the VALUES are fabricated.

    Using the actual historical credentials here would re-leak them into a new
    file — and this guard's own end-to-end test caught exactly that when this
    fixture was first written with the real ones. What the assertion depends on
    is the shape of each declaration, not the literal, so fabricated values test
    the same thing without adding a copy of a real secret to the repo.

    The values are also deliberately NOT canary/reserved-domain strings, since
    those are exempt by design and would make this test vacuously pass.

    Finally, the literals are ASSEMBLED at runtime rather than written out. A
    fixture of secret-shaped literals is itself a finding to any scanner — and
    exempting this file by path is precisely the location-based reasoning this
    module argues against, since it would blind the gate to a genuine secret
    committed here later. Assembling the values keeps the source free of any
    secret-shaped literal while the string the gate actually sees is unchanged.
    """
    pw = "Qx7" + "Lm2Rv9Tz4"
    tok = "Zt8Z6Kq2" + "Wm4Xp9Ln3Rv7Bd5Hf1Jc0Sg"
    mail = "acct7x9" + "@" + "mailhost-9271.zz"
    apik = "sk-" + "0000zzzz1111yyyy2222xxxx"
    ghk = "ghp_" + "0000zzzz1111yyyy2222"
    body = (
        f'EMAIL: str = "{mail}"\n'                       # 1
        f'PASSWORD: str = "{pw}"\n'                      # 2
        f'SESSION_TOKEN: str = "{tok}"\n'                # 3
        'import os\n'                                    # 4
        f'os.environ["NOTEGPT_PASSWORD"] = "{pw}"\n'     # 5
        f'os.environ["NOTEGPT_EMAIL"] = "{mail}"\n'      # 6
        f'API_KEY = "{apik}"\n'                          # 7
        f'GH = "{ghk}"\n'                                # 8
    )
    findings = _run_secret_scan(None, body)
    flagged = {f["line"] for f in findings}
    expected = {1, 2, 3, 5, 6, 7, 8}
    missed = expected - flagged
    assert not missed, f"real secrets NOT detected on lines {sorted(missed)}: {findings}"


def test_secret_scan_reports_only_real_secrets_in_provider_package():
    """
    The provider package must be clean under the gate. This is the end-to-end
    assertion: it fails both if a secret is committed AND if the gate regresses
    into flagging the correct env-var-name pattern.
    """
    import sys

    sys.path.insert(0, str(REPO_ROOT / ".connect" / "tools"))
    try:
        import secret_scan
    finally:
        sys.path.pop(0)

    package = REPO_ROOT / "providers" / "real" / "notegpt"
    findings = []
    for path in package.rglob("*.py"):
        findings.extend(secret_scan.scan_file(path))
    assert not findings, f"provider package not clean under secret_scan: {findings}"


# ==============================================================================
# P2 — ignored-but-tracked build artifacts
# ==============================================================================
# `.gitignore` listing a path does NOT untrack files already in the index; git
# applies ignore rules only to untracked paths. So `.pytest_cache/` sat in
# `.gitignore:12` while 5 of its files stayed tracked, and every test run
# produced phantom diffs in `lastfailed`/`nodeids` — noise that hides real
# changes in review and invites `git add -A` to commit whatever else appears.
#
# `git check-ignore` alone cannot catch this: it answers "would this be
# ignored", which is TRUE for these files. The contradiction is only visible by
# intersecting the ignore rules with the actual index, which is what this does.
def test_no_tracked_files_are_gitignored():
    """
    A file that is both tracked AND ignored is a contradiction: the repo says
    "do not track this" while tracking it. `git ls-files -i -c --exclude-standard`
    reports exactly that intersection.
    """
    result = subprocess.run(
        ["git", "ls-files", "-i", "-c", "--exclude-standard"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"git unavailable: {result.stderr.strip()}")

    offenders = [ln for ln in result.stdout.splitlines() if ln.strip()]
    assert not offenders, (
        "these files are tracked despite matching .gitignore — untrack with "
        f"`git rm -r --cached <path>`: {offenders}"
    )


def test_archive_scripts_read_credentials_from_env():
    """
    P3 — the 29 secrets ROUND2 §0 found in projects/ngpt/ were REWRITTEN to
    `os.environ.get("NOTEGPT_*", "")` rather than deleted, to keep the archive
    usable as a reference. Nothing imports those archive scripts, so a later
    edit (or a copy-paste from the still-public gist) could reintroduce a
    literal secret and the whole suite would stay green. This asserts the
    rewritten state directly.

    Why the empty-string default matters, and why it is asserted here:
    the archive guards login with `if not Config.EMAIL or not Config.PASSWORD`.
    A cosmetic placeholder default such as "YOUR_EMAIL_HERE" is truthy, so that
    guard would pass and the script would attempt a login with a fake value —
    the rewrite would look right and behave wrong. Only "" preserves the
    original control flow.

    Matching mirrors test_no_hardcoded_credentials_in_package: assignment
    TARGETS via AST, never a substring scan, so `EMAIL`, `self.EMAIL` and
    `os.environ["..."] = ...` all reduce to the same shape.
    """
    archive_root = REPO_ROOT / "projects" / "ngpt"
    if not archive_root.is_dir():
        pytest.skip("projects/ngpt/ not present")

    sensitive = re.compile(r"PASSWORD|PASSWD|PWD|TOKEN|SECRET|API_?KEY|EMAIL", re.I)

    def target_names(node):
        targets = [node.target] if isinstance(node, ast.AnnAssign) else node.targets
        for tgt in targets:
            if isinstance(tgt, ast.Name):
                yield tgt.id
            elif isinstance(tgt, ast.Attribute):
                yield tgt.attr
            elif isinstance(tgt, ast.Subscript):
                key = tgt.slice
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    yield key.value

    offenders = []
    for path in sorted(archive_root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = getattr(node, "value", None)
            if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                continue
            # "" is the intended post-rewrite state, not a secret.
            if value.value == "":
                continue
            # An env-var NAME is not a credential VALUE (same structural
            # exemption proven narrow in test_no_hardcoded_credentials_in_package).
            if re.fullmatch(r"[A-Z][A-Z0-9_]*", value.value):
                continue
            for name in target_names(node):
                if sensitive.search(name):
                    rel = path.relative_to(REPO_ROOT)
                    offenders.append(f"{rel}:{node.lineno} -> {name}")

    assert not offenders, (
        "literal credentials reintroduced into the reference archive — rewrite "
        "them with `python .connect/tools/rewrite_secrets.py --apply`: "
        f"{offenders}"
    )
