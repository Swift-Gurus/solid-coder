"""Tests for mcp-server/modes.py — the pipeline mode → load config registry."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mcp-server"))
import modes  # noqa: E402


class TestModesRegistry(unittest.TestCase):
    def test_all_expected_modes_present(self):
        expected = {"code", "review", "planner", "synth-impl", "synth-fixes"}
        self.assertEqual(set(modes.MODES.keys()), expected)

    def test_every_mode_has_required_keys(self):
        required = {"profile", "exclude", "aggregation", "description", "loads"}
        for name, cfg in modes.MODES.items():
            with self.subTest(mode=name):
                self.assertEqual(set(cfg.keys()) >= required, True,
                                 f"{name} missing: {required - set(cfg.keys())}")

    def test_profile_values_are_valid(self):
        for name, cfg in modes.MODES.items():
            with self.subTest(mode=name):
                self.assertIn(cfg["profile"], ["code", "review"])

    def test_aggregation_values_are_valid(self):
        for name, cfg in modes.MODES.items():
            with self.subTest(mode=name):
                self.assertIn(cfg["aggregation"], ["all", "per-principle"])

    def test_loads_sections_are_known(self):
        valid_sections = set(modes.SECTION_LABELS.keys())
        for name, cfg in modes.MODES.items():
            with self.subTest(mode=name):
                for section in cfg["loads"]:
                    self.assertIn(section, valid_sections,
                                  f"{name} declares unknown section: {section}")

    def test_exclude_sections_are_known(self):
        valid_sections = set(modes.SECTION_LABELS.keys())
        for name, cfg in modes.MODES.items():
            with self.subTest(mode=name):
                for section in cfg["exclude"]:
                    self.assertIn(section, valid_sections,
                                  f"{name} excludes unknown section: {section}")

    def test_resolve_returns_config(self):
        cfg = modes.resolve("code")
        self.assertEqual(cfg["profile"], "code")
        self.assertIn("examples", cfg["exclude"])

    def test_resolve_unknown_raises(self):
        with self.assertRaises(KeyError):
            modes.resolve("nonexistent")

    def test_review_profile_is_review(self):
        self.assertEqual(modes.MODES["review"]["profile"], "review")

    def test_review_is_per_principle(self):
        self.assertEqual(modes.MODES["review"]["aggregation"], "per-principle")

    def test_section_labels_have_no_pipe(self):
        # pipe chars break markdown tables
        for key, label in modes.SECTION_LABELS.items():
            with self.subTest(section=key):
                self.assertNotIn("|", label)


if __name__ == "__main__":
    unittest.main()
