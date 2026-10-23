"""
solid-description: Validates that configuration validation detects and rejects invalid input.
solid-category: unit-test
"""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
from pydantic import ValidationError

ensure_on_path(
    Path(__file__).resolve().parents[3] / "mcp-server" / "hooks",
    Path(__file__).resolve().parent,
)

from _config_section_stub import ConfigSectionStub
from solid_coder_config import SolidCoderConfig
from solid_coder_config_error import SolidCoderConfigError
from solid_coder_config_loader import SolidCoderConfigLoader


class TestValidationCatchesMistakes(unittest.TestCase):
    """extra='forbid' + typed fields turn silent misconfiguration into a loud, field-level error."""

    def test_wrong_type_raises_with_field_name(self):
        with (
            ConfigSectionStub(llm={"timeout": "soon"}),
            self.assertRaises(SolidCoderConfigError) as ctx,
        ):
            SolidCoderConfigLoader().load()
        self.assertIn("llm.timeout", str(ctx.exception))

    def test_unknown_key_raises_instead_of_being_ignored(self):
        with (
            ConfigSectionStub(llm={"tiemout": 5}),
            self.assertRaises(SolidCoderConfigError) as ctx,
        ):
            SolidCoderConfigLoader().load()
        self.assertIn("tiemout", str(ctx.exception))

    def test_unknown_key_in_hook_section_raises(self):
        with (
            ConfigSectionStub(hooks={"pre_write_gate": {"exclud": ["x"]}}),
            self.assertRaises(SolidCoderConfigError),
        ):
            SolidCoderConfigLoader().load()

    def test_unknown_top_level_section_raises(self):
        with self.assertRaises(ValidationError):
            SolidCoderConfig.model_validate({"llms": {"backend": "claude"}})

    def test_flow_engine_permitted_executables_loads(self):
        with ConfigSectionStub(flow_engine={"permitted_executables": ["python3"]}):
            config = SolidCoderConfigLoader().load()
        self.assertEqual(config.flow_engine.permitted_executables, ["python3"])

    def test_unknown_key_in_flow_engine_section_raises(self):
        with (
            ConfigSectionStub(flow_engine={"permited_executables": ["python3"]}),
            self.assertRaises(SolidCoderConfigError),
        ):
            SolidCoderConfigLoader().load()

    def test_feature_flags_flow_plain_text_response_loads(self):
        with ConfigSectionStub(feature_flags={"flow_plain_text_response": False}):
            config = SolidCoderConfigLoader().load()
        self.assertEqual(config.feature_flags.flow_plain_text_response, False)

    def test_feature_flags_flow_plain_text_response_defaults_to_true(self):
        with ConfigSectionStub():
            config = SolidCoderConfigLoader().load()
        self.assertEqual(config.feature_flags.flow_plain_text_response, True)

    def test_unknown_key_in_feature_flags_section_raises(self):
        with (
            ConfigSectionStub(feature_flags={"flow_plain_text_respons": True}),
            self.assertRaises(SolidCoderConfigError),
        ):
            SolidCoderConfigLoader().load()


if __name__ == "__main__":
    unittest.main()
