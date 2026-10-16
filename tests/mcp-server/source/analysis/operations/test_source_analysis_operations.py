import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from harness.project_context import ProjectDirectory
from source.analysis.matching.source_requirement_matches import SourceRequirementMatches
from source.analysis.operations.match_source_requirements_input import MatchSourceRequirementsInput
from source.analysis.operations.resolve_source_relationships_input import ResolveSourceRelationshipsInput
from source.analysis.operations.source_relationship_operation_result import SourceRelationshipOperationResult
from source.analysis.relationships.source_relationship_inventory import SourceRelationshipInventory
from source.analyze_source_input import AnalyzeSourceInput
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.source_operation_registrations_factory import SourceOperationRegistrationsFactory
from source.text_analysis_source import TextAnalysisSource


"""
solid-name: TestSourceAnalysisOperations
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies registered source operations preserve inspected snapshots and uncertainty while rejecting invalid relationship requests.
"""
class TestSourceAnalysisOperations(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.analysis = SourceAnalysisOperationFactory().make()
        registrations = SourceOperationRegistrationsFactory(ProjectDirectory(path=self.root)).make()
        self.relationships = next(item for item in registrations if item.name == "source.resolve_relationships")
        self.matching = next(item for item in registrations if item.name == "source.match_requirements")
        self.request = ResolveSourceRelationshipsInput(analyses=[
            self.analysis.execute(AnalyzeSourceInput(source=TextAnalysisSource(
                virtual_path=str(self.root / "Interface.swift"),
                text="protocol Reading { func read(id: Int) -> String }",
            ))),
            self.analysis.execute(AnalyzeSourceInput(source=TextAnalysisSource(
                virtual_path=str(self.root / "Store.swift"),
                text="struct Store: Reading {}",
            ))),
            self.analysis.execute(AnalyzeSourceInput(source=TextAnalysisSource(
                virtual_path=str(self.root / "Store+Reading.swift"),
                text='extension Store { func read(id value: Int) -> String { "ok" } }',
            ))),
        ])

    def test_registered_relationship_contract_accepts_and_preserves_prospective_snapshots(self) -> None:
        decoded = self.relationships.input_model.model_validate_json(self.request.model_dump_json())

        result = self.relationships.handler.execute(decoded).result

        self.assertEqual(result.analyses, self.request.analyses)
        self.assertEqual([item.reference.kind.value for item in result.relationships], ["inherited_type", "extension_target"])
        self.assertEqual(result.verification, "unverified_candidates")
        self.assertFalse((self.root / "Store.swift").exists())

    def test_matching_contract_retains_extension_owner_and_member_evidence(self) -> None:
        inventory = self.relationships.handler.execute(self.request).result
        request = MatchSourceRequirementsInput(inventory=inventory, relationship=inventory.relationships[0])
        decoded = self.matching.input_model.model_validate_json(request.model_dump_json())

        result = self.matching.handler.execute(decoded)

        self.assertEqual(result.inventory, inventory)
        self.assertEqual(result.matches[0].status.value, "candidate")
        self.assertEqual(result.matches[0].candidates[0].owner.source_identity, inventory.analyses[2].source_identity)
        self.assertEqual(result.matches[0].candidates[0].member, inventory.analyses[2].units[0].members[0])

    def test_missing_implementation_remains_unresolved_after_output_serialization(self) -> None:
        inventory = self.relationships.handler.execute(ResolveSourceRelationshipsInput(analyses=self.request.analyses[:2])).result
        request = MatchSourceRequirementsInput(inventory=inventory, relationship=inventory.relationships[0])

        result = self.matching.handler.execute(request)
        restored = self.matching.output_model.model_validate_json(result.model_dump_json())

        self.assertEqual(restored, result)
        self.assertEqual(restored.matches[0].status.value, "unresolved")
        self.assertEqual(restored.matches[0].candidates, [])
        self.assertIn("not established", restored.matches[0].reason)

    def test_relationship_output_round_trips_without_claiming_complete_discovery(self) -> None:
        result = self.relationships.handler.execute(self.request)

        restored = self.relationships.output_model.model_validate_json(result.model_dump_json())

        self.assertEqual(restored, result)
        self.assertIs(self.relationships.output_model, SourceRelationshipOperationResult)
        self.assertIs(self.matching.output_model, SourceRequirementMatches)
        self.assertEqual(restored.result.scope, "supplied_top_level_sources")
        self.assertEqual(restored.relationships, restored.result.relationships)

    def test_duplicate_source_snapshots_are_rejected_by_registered_operation(self) -> None:
        request = ResolveSourceRelationshipsInput(analyses=[self.request.analyses[0], self.request.analyses[0]])

        with self.assertRaisesRegex(ValueError, "one snapshot"):
            self.relationships.handler.execute(request)

    def test_unrecorded_relationship_is_rejected_by_registered_operation(self) -> None:
        inventory = self.relationships.handler.execute(self.request).result
        request = MatchSourceRequirementsInput(
            inventory=SourceRelationshipInventory(analyses=inventory.analyses),
            relationship=inventory.relationships[0],
        )

        with self.assertRaisesRegex(ValueError, "recorded"):
            self.matching.handler.execute(request)

    def test_extension_target_cannot_be_submitted_as_an_inherited_requirement(self) -> None:
        inventory = self.relationships.handler.execute(self.request).result
        request = MatchSourceRequirementsInput(inventory=inventory, relationship=inventory.relationships[1])

        with self.assertRaisesRegex(ValueError, "inherited"):
            self.matching.handler.execute(request)

    def test_registration_rejects_unknown_input_fields(self) -> None:
        with self.assertRaises(ValidationError):
            self.relationships.input_model.model_validate({"analyses": [], "complete": True})

    def test_matching_registration_requires_inventory_and_relationship(self) -> None:
        with self.assertRaises(ValidationError):
            self.matching.input_model.model_validate({})
