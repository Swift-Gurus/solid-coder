"""Uses real project TOML to verify the shared exclusion policy."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from gate.default_exclusion_checker_factory import DefaultExclusionCheckerFactory


class TestConfiguredExclusionPolicy(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="configured-exclusions-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / ".git").mkdir()
        (self.root / ".solid-coder").mkdir()
        (self.root / ".solid-coder" / "config.toml").write_text(
            '[hooks.pre_write_gate]\nexclude = ["Vendor/**/*.swift", "Tests/**"]\n'
        )

    def test_configured_pattern_is_retained_for_audit(self):
        policy = DefaultExclusionCheckerFactory().create(self.root)
        source = str(self.root / "Vendor" / "Package" / "Client.swift")
        self.assertTrue(policy.is_excluded(source))
        self.assertEqual(policy.matched_pattern(source), "Vendor/**/*.swift")
        self.assertFalse(
            policy.is_excluded(str(self.root / "Vendor" / "Package" / "manifest.json"))
        )
        self.assertIsNone(
            policy.matched_pattern(str(self.root / "Sources" / "Client.swift"))
        )

    def test_nested_project_override_uses_existing_loader_precedence(self):
        nested = self.root / "App"
        (nested / ".solid-coder").mkdir(parents=True)
        (nested / ".solid-coder" / "config.toml").write_text(
            '[hooks.pre_write_gate]\nexclude = ["Generated/**"]\n'
        )
        policy = DefaultExclusionCheckerFactory().create(nested)
        self.assertEqual(
            policy.matched_pattern(str(nested / "Generated" / "Client.swift")),
            "Generated/**",
        )
        self.assertFalse(policy.is_excluded(str(nested / "Vendor" / "Client.swift")))
