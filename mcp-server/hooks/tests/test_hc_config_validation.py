"""
solid-description: Validates that configuration validation detects and rejects invalid input.
solid-category: unit-test
"""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from _config_section_stub import ConfigSectionStub  # noqa: E402
from hc_config_schema import load_config  # noqa: E402
from solid_coder_config import SolidCoderConfig  # noqa: E402
from solid_coder_config_error import SolidCoderConfigError  # noqa: E402


class TestValidationCatchesMistakes(unittest.TestCase):
    """extra='forbid' + typed fields turn silent misconfiguration into a loud, field-level error."""

    def test_wrong_type_raises_with_field_name(self):
        with ConfigSectionStub(llm={"timeout": "soon"}):
            with self.assertRaises(SolidCoderConfigError) as ctx:
                load_config()
        self.assertIn("llm.timeout", str(ctx.exception))

    def test_unknown_key_raises_instead_of_being_ignored(self):
        with ConfigSectionStub(llm={"tiemout": 5}):
            with self.assertRaises(SolidCoderConfigError) as ctx:
                load_config()
        self.assertIn("tiemout", str(ctx.exception))

    def test_unknown_key_in_hook_section_raises(self):
        with ConfigSectionStub(hooks={"pre_write_gate": {"exclud": ["x"]}}):
            with self.assertRaises(SolidCoderConfigError):
                load_config()

    def test_unknown_top_level_section_raises(self):
        with self.assertRaises(Exception):
            SolidCoderConfig.model_validate({"llms": {"backend": "claude"}})

    def test_flow_engine_permitted_executables_loads(self):
        with ConfigSectionStub(flow_engine={"permitted_executables": ["python3"]}):
            config = load_config()
        self.assertEqual(config.flow_engine.permitted_executables, ["python3"])

    def test_unknown_key_in_flow_engine_section_raises(self):
        with ConfigSectionStub(flow_engine={"permited_executables": ["python3"]}):
            with self.assertRaises(SolidCoderConfigError):
                load_config()


if __name__ == "__main__":
    unittest.main()
