"""Tests source metadata configuration through real project TOML files."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from source.frontmatter.frontmatter_category_resolver import FrontmatterCategoryResolver
from source.frontmatter.frontmatter_config_parser import FrontmatterConfigParser

"""
solid-name: TestFrontmatterConfigInheritance
solid-category: integration-test
solid-spec: [SPEC-069]
solid-description: Verifies project category overrides follow root-to-leaf precedence and remain inside the project boundary.
"""


class TestFrontmatterConfigInheritance(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / "project"
        (self.project / ".git").mkdir(parents=True)
        self.sut = FrontmatterConfigParser()

    def test_nested_local_configuration_overrides_parent_and_bundled_defaults(
        self,
    ) -> None:
        self._write(self.project, "config.toml", "root-role")
        nested = self.project / "Sources"
        self._write(nested, "config.toml", "nested-role")
        self._write(nested, "config.local.toml", "local-role")
        config = self.sut.parse(nested)
        self.assertEqual(config.additional_categories, ["local-role"])
        categories = FrontmatterCategoryResolver().parse(config)
        self.assertIn("local-role", categories)
        self.assertIn("model", categories)
        self.assertNotIn("root-role", categories)
        self.assertNotIn("nested-role", categories)

    def test_configuration_above_git_boundary_is_not_inherited(self) -> None:
        self._write(self.root, "config.toml", "outside-role")
        self.assertEqual(self.sut.parse(self.project).additional_categories, [])

    def _write(self, directory: Path, filename: str, category: str) -> None:
        folder = directory / ".solid-coder"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / filename).write_text(
            f'[frontmatter]\nadditional_categories = ["{category}"]\n'
        )
