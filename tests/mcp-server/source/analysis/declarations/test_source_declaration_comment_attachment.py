"""
solid-name: TestSourceDeclarationCommentAttachment
solid-category: unit-test
solid-spec: [SPEC-069]
solid-description: Verifies the shared source inventory preserves declaration-owned frontmatter evidence.
"""

import unittest

from source.analysis.tree_sitter_swift_inventory_parser_factory import (
    TreeSitterSwiftInventoryParserFactory,
)


class TestSourceDeclarationCommentAttachment(unittest.TestCase):
    def test_declaration_signals_exclude_comments_literals_and_sibling_usage(
        self,
    ) -> None:
        inventory = (
            TreeSitterSwiftInventoryParserFactory()
            .make()
            .parse(
                'import SwiftUI\n// Task await View\nstruct User { let name = "View Task" }\n'
                'struct ProfileView: View { var body: some View { Text("Hi") } }',
            )
        )
        user, view = inventory.declarations
        self.assertNotIn("View", [signal.fact for signal in user.signals])
        self.assertNotIn("Task", [signal.fact for signal in user.signals])
        self.assertIn("View", [signal.fact for signal in view.signals])

    def test_inventory_keeps_wrong_name_metadata_with_its_declaration(self) -> None:
        inventory = (
            TreeSitterSwiftInventoryParserFactory()
            .make()
            .parse(
                "// solid-name: Wrong\nstruct Actual {}\nstruct Missing {}",
            )
        )

        actual, missing = inventory.declarations
        self.assertEqual(actual.unit.name, "Actual")
        self.assertEqual(
            [entry.fact for entry in actual.leading_comments],
            [
                "// solid-name: Wrong",
            ],
        )
        self.assertEqual(missing.leading_comments, [])

    def test_nested_metadata_does_not_replace_outer_metadata(self) -> None:
        inventory = (
            TreeSitterSwiftInventoryParserFactory()
            .make()
            .parse(
                "// solid-name: Outer\nstruct Outer {\n"
                "// solid-name: Inner\nstruct Inner {}\n}",
            )
        )

        outer, inner = inventory.declarations
        self.assertEqual(
            [entry.fact for entry in outer.leading_comments],
            [
                "// solid-name: Outer",
            ],
        )
        self.assertEqual(
            [entry.fact for entry in inner.leading_comments],
            [
                "// solid-name: Inner",
            ],
        )
        self.assertEqual(inner.leading_comments[0].span.start, 3)
