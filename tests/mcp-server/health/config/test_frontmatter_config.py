"""
solid-name: TestFrontmatterConfig
solid-category: unit-test
solid-spec: [SPEC-069]
solid-description: Verifies project category configuration is validated and exposed by the existing configuration loader.
"""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from pydantic import ValidationError

sys.path.insert(
    0, str(Path(__file__).resolve().parents[4] / "mcp-server" / "health" / "config")
)

from frontmatter_config import FrontmatterConfig
from solid_coder_config_loader import SolidCoderConfigLoader


class TestFrontmatterConfig(unittest.TestCase):
    def test_invalid_custom_categories_are_rejected(self) -> None:
        for category in [
            "",
            "misc",
            "other",
            "stuff",
            "TODO",
            "Upper",
            "two words",
            "-name",
        ]:
            with self.subTest(category=category), self.assertRaises(ValidationError):
                FrontmatterConfig(additional_categories=[category])

    def test_existing_config_loader_exposes_typed_categories(self) -> None:
        with (
            TemporaryDirectory() as directory,
            patch(
                "solid_coder_config_loader.read_section",
                return_value={"additional_categories": ["domain-role"]},
            ) as read,
        ):
            read.side_effect = lambda section, **kwargs: (
                {"additional_categories": ["domain-role"]}
                if section == "frontmatter"
                else {}
            )
            config = SolidCoderConfigLoader().load(Path(directory))
        self.assertEqual(config.frontmatter.additional_categories, ["domain-role"])
