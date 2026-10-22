"""
solid-name: TestBindFrontmatterDescriptionsOperation
solid-category: unit-test
solid-spec: [SPEC-069]
solid-description: Verifies description classifications account for every required source identity exactly once with evidence.
"""

import unittest
from pathlib import Path

from harness.flow_validation_error import FlowValidationError
from harness.project_context import ProjectDirectory
from source.frontmatter.bind_frontmatter_descriptions_input import BindFrontmatterDescriptionsInput
from source.frontmatter.frontmatter_operation_registrations_factory import FrontmatterOperationRegistrationsFactory
from source.frontmatter.prepare_frontmatter_input import PrepareFrontmatterInput
from source.frontmatter.source_description_classification import SourceDescriptionClassification
from findings.metric_additional_info import MetricAdditionalInfo
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.swift_source_analyzer_factory import SwiftSourceAnalyzerFactory


class TestBindFrontmatterDescriptionsOperation(unittest.TestCase):
    def setUp(self) -> None:
        registrations = FrontmatterOperationRegistrationsFactory(ProjectDirectory(path=Path("/unwritten-project"))).make()
        self.prepare = next(entry.handler for entry in registrations if entry.name == "source.prepare_frontmatter")
        self.bind = next(entry.handler for entry in registrations if entry.name == "source.bind_frontmatter_descriptions")
        analysis = SwiftSourceAnalyzerFactory().make().analyze(ResolvedAnalysisSource(
            identity="/unwritten-project/Target.swift", file_extension=".swift",
            text="// solid-name: Target\n// solid-category: service\n// solid-description: Provides deliveries.\nstruct Target {}",
        ))
        self.prepared = self.prepare.execute(PrepareFrontmatterInput(analysis=analysis))
        self.identity = self.prepared.descriptions[0].declaration_id

    def test_classifications_are_bound_without_model_counts(self) -> None:
        for classification in ["CAPABILITY", "IMPLEMENTATION_DETAIL", "VAGUE"]:
            with self.subTest(classification=classification):
                result = self.bind.execute(BindFrontmatterDescriptionsInput(entries=self.prepared.entries, targets=self.prepared.descriptions, classifications=[self._judgment(self.identity, classification)]))
                self.assertEqual(result.descriptions[0].classification, classification)
                self.assertEqual(result.descriptions[0].additional_info.evidence, "Provides deliveries.")

    def test_mechanical_failure_uses_the_shared_classification_record(self) -> None:
        entry = self.prepared.entries[0].model_copy(update={"bad_description": True})
        result = self.bind.execute(BindFrontmatterDescriptionsInput(
            entries=[entry], targets=[], classifications=[],
        ))
        self.assertEqual(len(result.descriptions), 1)
        decision = result.descriptions[0]
        self.assertEqual(decision.declaration_id, self.identity)
        self.assertEqual(decision.classification, "INVALID_FORMAT")
        self.assertIn("absent or fails", decision.additional_info.reasoning)
        self.assertIn("Target", decision.additional_info.evidence)

    def test_missing_duplicate_and_unrelated_judgments_are_rejected_with_replacement_guidance(self) -> None:
        for judgments in [[], [self._judgment(self.identity), self._judgment(self.identity)], [self._judgment("unknown")]]:
            with self.subTest(judgments=judgments), self.assertRaisesRegex(FlowValidationError, "complete replacement"):
                self.bind.execute(BindFrontmatterDescriptionsInput(entries=self.prepared.entries, targets=self.prepared.descriptions, classifications=judgments))

    def _judgment(self, identity: str, classification: str = "CAPABILITY") -> SourceDescriptionClassification:
        return SourceDescriptionClassification(declaration_id=identity, classification=classification,
            additional_info=MetricAdditionalInfo(reasoning="The wording describes the capability.", evidence="Provides deliveries."))
