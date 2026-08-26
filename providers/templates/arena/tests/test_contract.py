#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline contract tests for the disabled Arena.ai provider template.

Run directly with stdlib only:
    python3 providers/templates/arena/tests/test_contract.py

These tests intentionally do not simulate successful generation.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from providers.templates.arena import ArenaProvider, get_provider  # noqa: E402
from providers.templates.arena import errors as err  # noqa: E402
from providers.templates.arena.config import ArenaConfig  # noqa: E402
from providers.templates.arena.discovery import capabilities as caps  # noqa: E402


class ArenaTemplateContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = ArenaProvider(ArenaConfig())

    def test_public_surface_is_small_and_stable(self) -> None:
        import providers.templates.arena as package

        self.assertEqual(package.__all__, ["ArenaProvider", "get_provider"])
        self.assertEqual(package.__provider_id__, "arena")
        self.assertEqual(package.__status__, "template_disabled")

    def test_manifest_is_disabled_and_non_functional(self) -> None:
        manifest = self.provider.get_manifest()
        self.assertEqual(manifest["id"], "arena")
        self.assertEqual(manifest["status"], "template_disabled")
        self.assertTrue(manifest["is_template"])
        self.assertFalse(manifest["is_functional"])
        self.assertTrue(manifest["real_provider_required"])

    def test_manifest_and_capability_code_match(self) -> None:
        self.assertEqual(self.provider.get_manifest()["capabilities"], caps.get_capabilities())

    def test_template_is_not_routable(self) -> None:
        self.assertFalse(self.provider.is_routable())
        self.assertEqual(self.provider.get_capabilities_for_routing(), {})
        for name in caps.get_capabilities():
            self.assertFalse(caps.supports(name))

    def test_no_models_are_invented(self) -> None:
        self.assertEqual(self.provider.discover_models(), [])
        self.assertEqual(self.provider.get_manifest()["models"]["static_models"], [])

    def test_generation_is_rejected(self) -> None:
        result = self.provider.generate({"operation": "run_provider_agent", "prompt": "hello"})
        self.assertEqual(result["error"]["category"], err.PROVIDER_DISABLED)
        self.assertFalse(result["error"]["retryable"])

    def test_operation_function_is_rejected(self) -> None:
        from providers.templates.arena.operations.provider_agent import run_provider_agent

        result = run_provider_agent({"prompt": "hello"})
        self.assertEqual(result["error"]["category"], err.PROVIDER_DISABLED)

    def test_health_is_non_functional_without_network(self) -> None:
        health = self.provider.health_check()
        self.assertEqual(health["state"], "SUSPENDED")
        self.assertFalse(health["checked_live"])
        self.assertFalse(health["is_functional"])

    def test_credential_validation_checks_presence_only(self) -> None:
        self.assertEqual(self.provider.validate_credential()["state"], "INVALID")
        self.assertEqual(
            self.provider.validate_credential("opaque-ref")["state"], "PENDING"
        )

    def test_redaction_does_not_include_credential_reference(self) -> None:
        config = ArenaConfig(credential_ref="opaque-secret-reference")
        redacted = repr(config)
        self.assertNotIn("opaque-secret-reference", redacted)
        self.assertNotIn("opaque-secret-reference", repr(ArenaProvider(config)))

    def test_environment_is_not_required_or_mutated(self) -> None:
        before = os.environ.get("ARENA_CREDENTIAL_REF")
        _ = ArenaConfig.from_environment()
        self.assertEqual(os.environ.get("ARENA_CREDENTIAL_REF"), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
