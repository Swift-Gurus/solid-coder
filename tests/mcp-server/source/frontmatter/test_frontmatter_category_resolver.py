"""Tests effective source metadata vocabulary resolution."""

import unittest

from health.config.frontmatter_config import FrontmatterConfig
from source.frontmatter.frontmatter_category_resolver import FrontmatterCategoryResolver


"""
solid-name: TestFrontmatterCategoryResolver
solid-category: unit-test
solid-spec: [SPEC-069]
solid-description: Verifies project metadata categories extend the bundled vocabulary without duplicates.
"""
class TestFrontmatterCategoryResolver(unittest.TestCase):
    def test_project_categories_extend_the_registered_vocabulary(self) -> None:
        config = FrontmatterConfig(additional_categories=["domain-role", "service"])
        categories = FrontmatterCategoryResolver().parse(config)
        self.assertIn("service", categories)
        self.assertIn("model", categories)
        self.assertIn("domain-role", categories)
        self.assertEqual(categories.count("service"), 1)
        self.assertEqual(categories, sorted(categories))

    def test_default_configuration_preserves_registered_categories(self) -> None:
        self.assertIn("abstraction", FrontmatterCategoryResolver().parse(FrontmatterConfig()))
