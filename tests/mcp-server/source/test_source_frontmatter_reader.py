"""Tests typed reading of solid source frontmatter blocks."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from source.source_frontmatter import SourceFrontmatter
from source.source_frontmatter_reader_factory import SourceFrontmatterReaderFactory

"""
solid-name: TestSourceFrontmatterReader
solid-category: unit-test
solid-spec: [SPEC-040]
solid-description: Verifies comment-wrapped YAML frontmatter maps directly into typed source metadata.
"""


class TestSourceFrontmatterReader(unittest.TestCase):
    def setUp(self) -> None:
        self.reader = SourceFrontmatterReaderFactory().make()

    def test_reads_multiple_typed_frontmatter_blocks(self) -> None:
        frontmatter = self.reader.read(
            """
            // solid-name: UserFetcher
            // solid-category: service
            // solid-description: Fetches remote user data.
            // solid-tags: [networking, user]
            // solid-spec: [SPEC-040]
            struct UserFetcher {}

            // solid-name: UserCache
            // solid-category: model
            // solid-description: Stores fetched users.
            struct UserCache {}
            """
        )

        self.assertEqual(
            [entry.name for entry in frontmatter],
            ["UserFetcher", "UserCache"],
        )
        self.assertEqual(
            frontmatter[0].description,
            "Fetches remote user data.",
        )
        self.assertEqual(frontmatter[0].category, "service")
        self.assertEqual(frontmatter[0].tags, ["networking", "user"])
        self.assertEqual(frontmatter[0].specs, ["SPEC-040"])

    def test_returns_empty_collection_when_source_has_no_frontmatter(self) -> None:
        self.assertEqual(self.reader.read("struct UserCache {}\n"), [])

    def test_strict_comment_parsing_preserves_multiline_description(self) -> None:
        metadata = self.reader.parse(
            "/**\n solid-name: Target\n solid-description: >\n"
            "   Provides a reusable capability\n   for clients.\n solid-category: service\n */",
        )
        self.assertEqual(metadata.name, "Target")
        self.assertEqual(
            metadata.description.strip(), "Provides a reusable capability for clients."
        )

    def test_strict_comment_parsing_handles_inline_comment_wrappers(self) -> None:
        self.assertEqual(self.reader.parse("/** solid-name: Target */").name, "Target")

    def test_metadata_round_trips_through_typed_operation_outputs(self) -> None:
        metadata = self.reader.parse(
            "// solid-name: Target\n// solid-category: service"
        )
        self.assertEqual(
            SourceFrontmatter.model_validate(metadata.model_dump()), metadata
        )

    def test_preserves_plain_multiline_comment_descriptions(self) -> None:
        metadata = self.reader.parse(
            "/**\n solid-name: Target\n solid-description: Provides deliveries\n across supported regions.\n solid-category: service\n */"
        )
        self.assertEqual(
            metadata.description, "Provides deliveries across supported regions."
        )

    def test_strict_comment_parsing_distinguishes_absent_from_malformed(self) -> None:
        self.assertIsNone(self.reader.parse("// Ordinary documentation"))
        with self.assertRaises(FlowValidationError):
            self.reader.parse("// solid-name: [broken")

    def test_strict_comment_parsing_rejects_duplicate_fields(self) -> None:
        with self.assertRaises(FlowValidationError):
            self.reader.parse("// solid-category: model\n// solid-category: service")

    def test_returns_empty_collection_when_frontmatter_yaml_is_malformed(self) -> None:
        frontmatter = self.reader.read(
            """
            # solid-name: FindingComparerTests
            # solid-category: unit-test
            # solid-description: Covers these cases: exact and missing findings.
            class FindingComparerTests:
                pass
            """
        )

        self.assertEqual(frontmatter, [])

    def test_ignores_solid_prefixed_source_text_that_is_not_frontmatter(self) -> None:
        frontmatter = self.reader.read(
            '''
            name = f"solid-coder-{prefix}-{timestamp}.md"
            supported = ("solid-name:", "solid-description:")

            """
            solid-name: ArtifactWriter
            solid-category: service
            solid-description: Writes named artifacts.
            """
            class ArtifactWriter:
                pass
            '''
        )

        self.assertEqual(len(frontmatter), 1)
        self.assertEqual(frontmatter[0].name, "ArtifactWriter")


if __name__ == "__main__":
    unittest.main()
