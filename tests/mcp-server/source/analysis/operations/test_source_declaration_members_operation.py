import unittest

from source.analysis.matching.source_declaration_members import SourceDeclarationMembers
from source.analysis.operations.source_analysis_operation_registrations_factory import (
    SourceAnalysisOperationRegistrationsFactory,
)
from source.analysis.operations.source_declaration_members_input import (
    SourceDeclarationMembersInput,
)
from source.analysis.relationships.source_reference_candidate_resolver import (
    SourceReferenceCandidateResolver,
)
from source.analysis.relationships.source_relationship_resolver import (
    SourceRelationshipResolver,
)
from source.analyze_source_input import AnalyzeSourceInput
from source.search_target_granularity import SearchTargetGranularity
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.source_unit_identity import SourceUnitIdentity
from source.text_analysis_source import TextAnalysisSource

"""
solid-name: TestSourceDeclarationMembersOperation
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies declared and extension member contributions preserve ownership uncertainty, unsupported signatures, source evidence, and snapshot identity.
"""


class TestSourceDeclarationMembersOperation(unittest.TestCase):
    def setUp(self) -> None:
        self.analysis = SourceAnalysisOperationFactory().make()
        self.relationships = SourceRelationshipResolver(
            SourceReferenceCandidateResolver()
        )
        self.registration = next(
            item
            for item in SourceAnalysisOperationRegistrationsFactory().make()
            if item.name == "source.declaration_members"
        )

    def request(self, *sources: str) -> SourceDeclarationMembersInput:
        inventory = self.relationships.resolve(
            [
                self.analysis.execute(
                    AnalyzeSourceInput(
                        source=TextAnalysisSource(
                            virtual_path=f"Source{index}.swift",
                            text=code,
                        )
                    )
                )
                for index, code in enumerate(sources)
            ]
        )
        return SourceDeclarationMembersInput(
            inventory=inventory,
            declaration=SourceUnitIdentity(
                source_identity=inventory.analyses[0].source_identity,
                unit_identity=inventory.analyses[0].units[0].identity,
            ),
        )

    def test_ambiguous_extension_owner_remains_unresolved(self) -> None:
        result = self.registration.handler.execute(
            self.request(
                "protocol Reading { func read() }",
                "protocol Reading { func other() }",
                "extension Reading { func extra() {} }",
            )
        )

        self.assertEqual(
            [member.role.value for member in result.members], ["declared", "unresolved"]
        )
        self.assertEqual(
            result.members[1].reference.relationships[0].status.value, "ambiguous"
        )
        self.assertIn("Multiple", result.members[1].reason)

    def test_conditional_default_keeps_its_match_but_is_unresolved(self) -> None:
        result = self.registration.handler.execute(
            self.request(
                "protocol Reading { func read() }",
                "extension Reading where Self: Other { func read() {} }",
            )
        )

        self.assertEqual(result.members[1].role.value, "unresolved")
        self.assertEqual(
            result.members[1].matching_declarations,
            [result.members[0].reference.member],
        )

    def test_generic_signature_is_not_reported_as_an_additional_member(self) -> None:
        result = self.registration.handler.execute(
            self.request(
                "protocol Reading { func read<T>(_ item: T) }",
                "extension Reading { func read<T>(_ item: T) {} }",
            )
        )

        self.assertEqual(result.members[1].role.value, "unresolved")
        self.assertEqual(result.members[1].matching_declarations, [])

    def test_inherited_requirements_are_not_added_to_direct_inventory(self) -> None:
        result = self.registration.handler.execute(
            self.request(
                "protocol Reading: Base { func close() }",
                "protocol Base { func read() }",
                "extension Reading { func read() {} }",
            )
        )

        self.assertEqual(
            [member.reference.member.name for member in result.members],
            ["close", "read"],
        )
        self.assertEqual(result.members[1].role.value, "unresolved")
        self.assertIn("inherited", result.members[1].reason)

    def test_property_and_subscript_defaults_use_shared_signature_matching(
        self,
    ) -> None:
        result = self.registration.handler.execute(
            self.request(
                "protocol Reading { var count: Int { get }; subscript(index: Int) -> String { get } }",
                'extension Reading { var count: Int { 0 }; subscript(value: Int) -> String { "ok" } }',
            )
        )

        self.assertEqual(
            [member.role.value for member in result.members],
            ["declared", "declared", "implementation", "implementation"],
        )

    def test_visibility_is_preserved_for_workflow_selection(self) -> None:
        result = self.registration.handler.execute(
            self.request(
                "protocol Reading { func read() }",
                "extension Reading { private func hidden() {}; fileprivate func helper() {} }",
            )
        )

        self.assertEqual(
            [member.reference.member.visibility.value for member in result.members[1:]],
            ["private", "fileprivate"],
        )
        self.assertEqual(
            [member.role.value for member in result.members[1:]],
            ["additional", "additional"],
        )

    def test_empty_declaration_has_an_empty_member_collection(self) -> None:
        result = self.registration.handler.execute(self.request("protocol Reading {}"))

        self.assertEqual(result.members, [])
        self.assertEqual(result.inventory.verification, "unverified_candidates")

    def test_unknown_declaration_is_rejected(self) -> None:
        request = self.request("protocol Reading { func read() }")
        invalid = SourceDeclarationMembersInput(
            inventory=request.inventory,
            declaration=SourceUnitIdentity(
                source_identity=request.declaration.source_identity,
                unit_identity="missing",
            ),
        )

        with self.assertRaisesRegex(ValueError, "recorded declaration"):
            self.registration.handler.execute(invalid)

    def test_file_identity_cannot_replace_the_recorded_unit_identity(self) -> None:
        request = self.request("protocol Reading { func read() }")
        invalid = SourceDeclarationMembersInput(
            inventory=request.inventory,
            declaration=SourceUnitIdentity(
                source_identity=request.declaration.source_identity,
                unit_identity=request.declaration.unit_identity,
                granularity=SearchTargetGranularity.FILE,
            ),
        )

        with self.assertRaisesRegex(ValueError, "recorded declaration"):
            self.registration.handler.execute(invalid)

    def test_result_round_trips_with_original_member_and_ownership_evidence(
        self,
    ) -> None:
        request = self.request(
            "protocol Reading { func read() }", "extension Reading { func read() {} }"
        )
        result = self.registration.handler.execute(request)

        restored = SourceDeclarationMembers.model_validate_json(
            result.model_dump_json()
        )

        self.assertEqual(restored, result)
        self.assertEqual(restored.inventory, request.inventory)
        self.assertEqual(
            restored.members[1].reference.member,
            request.inventory.analyses[1].units[0].members[0],
        )
