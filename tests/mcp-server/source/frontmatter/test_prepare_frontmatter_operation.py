"""
solid-name: TestPrepareFrontmatterOperation
solid-category: unit-test
solid-spec: [SPEC-069]
solid-description: Verifies deterministic metadata facts and exclusions use exact prospective source and project categories.
"""

import unittest
from pathlib import Path
from unittest.mock import Mock

from harness.project_context import ProjectDirectory
from health.config.frontmatter_config import FrontmatterConfig
from source.frontmatter.declaration_stack_resolver import DeclarationStackResolver
from source.frontmatter.frontmatter_category_resolver import FrontmatterCategoryResolver
from source.frontmatter.prepare_frontmatter_input import PrepareFrontmatterInput
from source.frontmatter.prepare_frontmatter_operation import PrepareFrontmatterOperation
from source.frontmatter.stack_registration import StackRegistration
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.source_frontmatter_reader_factory import SourceFrontmatterReaderFactory
from source.swift_source_analyzer_factory import SwiftSourceAnalyzerFactory


class TestPrepareFrontmatterOperation(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = Mock()
        self.policy.parse.return_value = FrontmatterConfig(additional_categories=["domain-role"])
        self.registrations = [StackRegistration(tag="swiftui", file_extensions=[".swift"], modules=["SwiftUI"], signals=["View", "Text"])]
        self.sut = PrepareFrontmatterOperation(
            metadata=SourceFrontmatterReaderFactory().make(),
            stacks=DeclarationStackResolver(self.registrations),
            configuration=self.policy,
            project_directory=ProjectDirectory(path=Path("/project")),
            stack_registrations=self.registrations,
            categories=FrontmatterCategoryResolver(),
        )

    def test_missing_metadata_is_measured_without_description_target(self) -> None:
        prepared = self._prepare("struct Target { let value: String }")
        self.assertEqual(len(prepared.entries), 1)
        self.assertFalse(prepared.entries[0].has_frontmatter)
        self.assertFalse(prepared.entries[0].missing_exempt)
        self.assertEqual(prepared.descriptions, [])
        self.assertEqual(prepared.limitations, [])

    def test_wrong_name_does_not_hide_attached_metadata(self) -> None:
        prepared = self._prepare("// solid-name: Wrong\n// solid-category: service\n// solid-description: Provides deliveries.\nstruct Target {}")
        entry = prepared.entries[0]
        self.assertTrue(entry.has_frontmatter)
        self.assertFalse(entry.name_matches)
        self.assertTrue(entry.category_registered)
        self.assertEqual(prepared.descriptions[0].name, "Target")

    def test_registered_project_category_is_accepted_and_unknown_is_not(self) -> None:
        for category, valid in [("domain-role", True), ("service", True), ("unregistered", False), ("misc", False)]:
            with self.subTest(category=category):
                prepared = self._prepare(f"// solid-name: Target\n// solid-category: {category}\nstruct Target {{}}")
                self.assertEqual(prepared.entries[0].category_registered, valid)
                self.assertIn("domain-role", prepared.categories)
        self.policy.parse.assert_called_with(Path("/project"))

    def test_stack_is_checked_per_declaration_not_per_file_import(self) -> None:
        prepared = self._prepare("import SwiftUI\n// solid-name: User\n// solid-category: model\nstruct User {}\n// solid-name: Profile\n// solid-category: screen\nstruct Profile: View { var body: some View { Text(\"Hi\") } }")
        self.assertTrue(prepared.entries[0].stack_matches)
        self.assertFalse(prepared.entries[1].stack_matches)
        self.assertEqual(prepared.entries[0].stack_evidence, [])

    def test_structural_missing_exclusions_are_not_model_judgments(self) -> None:
        prepared = self._prepare("private struct Helper {}\nextension Helper {}\nstruct Main {}")
        self.assertEqual([entry.missing_exempt for entry in prepared.entries], [True, True, False])

    def test_nested_types_are_not_top_level_frontmatter_targets(self) -> None:
        prepared = self._prepare("struct Outer { struct Inner {} }")
        self.assertEqual([entry.declaration.unit.name for entry in prepared.entries], ["Outer"])

    def test_malformed_metadata_remains_an_explicit_limitation(self) -> None:
        prepared = self._prepare("// solid-name: [broken\nstruct Target {}")
        self.assertTrue(prepared.limitations)
        self.assertIn("Target", prepared.limitations[0])

    def test_missing_and_wrong_contract_prefix_are_mechanical_description_failures(self) -> None:
        prepared = self._prepare("// solid-name: Target\n// solid-category: abstraction\n// solid-description: Provides an interface.\nprotocol Target {}")
        self.assertTrue(prepared.entries[0].bad_description)
        self.assertEqual(prepared.descriptions, [])

    def _prepare(self, text: str):
        analysis = SwiftSourceAnalyzerFactory().make().analyze(ResolvedAnalysisSource(identity="/unwritten/Target.swift", file_extension=".swift", text=text))
        return self.sut.execute(PrepareFrontmatterInput(analysis=analysis))
