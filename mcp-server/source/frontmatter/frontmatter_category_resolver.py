"""Resolves the effective source metadata category vocabulary."""

from health.config.frontmatter_config import FrontmatterConfig
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing


_CATEGORIES = frozenset({
    "abstraction", "network", "viewmodel", "model", "view-component", "screen",
    "modifier", "crud", "utility", "navigation", "service", "unit-test", "ui-test",
    "factory", "builder", "adapter", "boundary-adapter", "integration-test", "test-support",
})


"""
solid-name: FrontmatterCategoryResolver
solid-category: service
solid-spec: [SPEC-069]
solid-description: Resolves the registered metadata categories with project additions without duplicates.
"""
class FrontmatterCategoryResolver(SourceSyntaxParsing[FrontmatterConfig, list[str]]):
    def parse(self, source: FrontmatterConfig) -> list[str]:
        return sorted(_CATEGORIES.union(source.additional_categories))
