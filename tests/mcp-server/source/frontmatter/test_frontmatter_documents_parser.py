"""
solid-name: TestFrontmatterDocumentsParser
solid-category: unit-test
solid-spec: [SPEC-069]
solid-description: Verifies comment-wrapped metadata discovery preserves document boundaries and description continuations.
"""

import unittest

from source.frontmatter.frontmatter_documents_parser import FrontmatterDocumentsParser


class TestFrontmatterDocumentsParser(unittest.TestCase):
    def test_keeps_document_boundaries_separate_from_declaration_names(self) -> None:
        documents = FrontmatterDocumentsParser().parse("// solid-name: Wrong\nstruct Target {}\n// solid-name: Other\nstruct Other {}")
        self.assertEqual(documents, ["solid-name: Wrong", "solid-name: Other"])

    def test_retains_description_continuation(self) -> None:
        documents = FrontmatterDocumentsParser().parse("/**\n solid-name: Target\n solid-description: Provides deliveries\n across regions.\n */")
        self.assertEqual(documents, ["solid-name: Target\nsolid-description: Provides deliveries\n  across regions."])

    def test_source_strings_are_not_metadata(self) -> None:
        self.assertEqual(FrontmatterDocumentsParser().parse('let text = "solid-name: Target"'), [])
