"""Tests the opt-in submission envelope configuration."""

import sys
import unittest
from pathlib import Path

from pydantic import ValidationError

_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPOSITORY_ROOT / "mcp-server" / "health" / "config"))
sys.path.insert(0, str(_REPOSITORY_ROOT / "tests" / "mcp-server" / "hooks"))

from _config_section_stub import ConfigSectionStub
from feature_flags_config import FeatureFlagsConfig
from solid_coder_config_loader import SolidCoderConfigLoader

"""
solid-name: TestFlowSubmissionFormatConfig
solid-category: unit-test
solid-spec: [SPEC-068]
solid-description: Verifies default and opt-in flow submission formats use validated feature configuration.
"""


class TestFlowSubmissionFormatConfig(unittest.TestCase):
    def test_default_is_nested(self) -> None:
        self.assertEqual(FeatureFlagsConfig().flow_submission_format, "nested")

    def test_loads_flat_array_through_existing_config(self) -> None:
        with ConfigSectionStub(feature_flags={"flow_submission_format": "flat_array"}):
            config = SolidCoderConfigLoader().load()

        self.assertEqual(config.feature_flags.flow_submission_format, "flat_array")

    def test_rejects_unknown_format(self) -> None:
        with self.assertRaises(ValidationError):
            FeatureFlagsConfig(flow_submission_format="markdown")
