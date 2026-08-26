# -*- coding: utf-8 -*-
"""
================================================================================
NoteGPT Tests — shared fixtures (T-05)
================================================================================
Puts the repository root on sys.path (mirroring test_contract.py) and exposes
the MockTransport as reusable fixtures so no test re-implements mock logic.

Nothing here is imported by the provider package.
================================================================================
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from providers.real.notegpt.config import NoteGPTConfig            # noqa: E402
from providers.real.notegpt.runtime import session as session_mod  # noqa: E402

from . import mock_transport as mt                                 # noqa: E402


@pytest.fixture()
def config() -> NoteGPTConfig:
    """Config with no credentials — guarantees no login/network path is taken."""
    return NoteGPTConfig()


@pytest.fixture()
def session():
    """A fresh conversation session with a zeroed continue counter."""
    return session_mod.new_session()


@pytest.fixture()
def transport_factory():
    """Build a MockTransport with explicit stream/continue scripts."""

    def _make(**kwargs) -> mt.MockTransport:
        return mt.MockTransport(**kwargs)

    return _make


@pytest.fixture()
def lines():
    """Direct access to the SSE wire-line builders."""
    return mt
