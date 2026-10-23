"""Tests unified configuration loading through the real TOML boundary."""

import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

sys.path.insert(
    0, str(Path(__file__).resolve().parents[4] / "mcp-server" / "health" / "config")
)

from config_section_reading import ConfigSectionReading
from solid_coder_config_error import SolidCoderConfigError
from solid_coder_config_loader import SolidCoderConfigLoader

"""
solid-name: TestSolidCoderConfigLoader
solid-category: unit-test
solid-spec: [SPEC-069]
solid-description: Verifies typed configuration loading preserves hierarchical overrides, model profiles, injected file reads and field-level validation errors.
"""


class TestSolidCoderConfigLoader(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / ".git").mkdir()
        self.folder = self.root / ".solid-coder"
        self.folder.mkdir()
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        self.sut = SolidCoderConfigLoader()

    def test_empty_project_uses_typed_defaults(self) -> None:
        config = self.sut.load(self.root)
        self.assertEqual(config.feature_flags.health_check_mode.value, "workflow")
        self.assertEqual(config.frontmatter.additional_categories, [])

    def test_package_import_works_in_a_fresh_process_with_only_the_mcp_root(
        self,
    ) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; sys.path.insert(0, sys.argv[1]); "
                    "from health.config.solid_coder_config_loader import SolidCoderConfigLoader; "
                    "print(SolidCoderConfigLoader().load().frontmatter.additional_categories)"
                ),
                str(Path(__file__).resolve().parents[4] / "mcp-server"),
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "[]")

    def test_local_categories_and_mode_override_project_defaults(self) -> None:
        (self.folder / "config.toml").write_text(
            '[frontmatter]\nadditional_categories = ["root-role"]\n[feature_flags]\nhealth_check_mode = "workflow"\n'
        )
        (self.folder / "config.local.toml").write_text(
            '[frontmatter]\nadditional_categories = ["local-role"]\n[feature_flags]\nhealth_check_mode = "legacy"\n'
        )
        config = self.sut.load(self.root)
        self.assertEqual(config.frontmatter.additional_categories, ["local-role"])
        self.assertEqual(config.feature_flags.health_check_mode.value, "legacy")

    def test_invalid_fields_raise_the_existing_configuration_error(self) -> None:
        (self.folder / "config.toml").write_text('[llm]\ntimeout = "soon"\n')
        with self.assertRaisesRegex(SolidCoderConfigError, "llm.timeout"):
            self.sut.load(self.root)

    def test_profile_overrides_llm_without_replacing_project_categories(self) -> None:
        (self.folder / "config.toml").write_text(
            '[frontmatter]\nadditional_categories = ["domain-role"]\n[llm]\ntimeout = 10\n'
        )
        profile = self.root / "profile.toml"
        profile.write_text("[llm]\ntimeout = 73\n")
        with patch.dict(os.environ, {"SOLID_CODER_TEST_MODEL_PROFILE": str(profile)}):
            config = self.sut.load(self.root)
        self.assertEqual(config.llm.timeout, 73)
        self.assertEqual(config.frontmatter.additional_categories, ["domain-role"])

    def test_injected_section_reader_controls_loading(self) -> None:
        reader = Mock(spec=ConfigSectionReading)
        reader.side_effect = lambda section, **kwargs: (
            {"additional_categories": ["injected-role"]}
            if section == "frontmatter"
            else {}
        )
        config = SolidCoderConfigLoader(section_reader=reader).load(self.root)
        self.assertEqual(config.frontmatter.additional_categories, ["injected-role"])
