"""Tests for pre_write_gate.py — paths matching [hooks.pre_write_gate].exclude bypass all checks."""

import unittest
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from _gate_fixtures import HC, LONG_SWIFT, call_main, event
from hook_config import HookConfig
from solid_coder_config import SolidCoderConfig


class TestGateExclusion(unittest.TestCase):
    def test_excluded_path_allows_without_health_check(self):
        stub_config = SolidCoderConfig(hooks={"pre_write_gate": HookConfig(exclude=["tests/fixtures/**"])})
        with patch("hc_config.load_config", return_value=stub_config), patch(HC) as hc:
            code, out = call_main(event("Write", "/project/tests/fixtures/SRP/srp2-severe.swift", LONG_SWIFT))
        hc.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_non_excluded_path_runs_health(self):
        stub_config = SolidCoderConfig(hooks={"pre_write_gate": HookConfig(exclude=["tests/fixtures/**"])})
        with patch("hc_config.load_config", return_value=stub_config), patch(HC, return_value=[]) as hc:
            call_main(event("Write", "/src/Main.swift", LONG_SWIFT))
        hc.assert_called_once()

    def test_no_exclusions_runs_health_normally(self):
        with patch("hc_config.load_config", return_value=SolidCoderConfig()), patch(HC, return_value=[]) as hc:
            call_main(event("Write", "/src/Main.swift", LONG_SWIFT))
        hc.assert_called_once()


if __name__ == "__main__":
    unittest.main()
