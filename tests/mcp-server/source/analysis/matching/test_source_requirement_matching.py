"""Exercises bounded requirement matching through real source analysis."""

import unittest

from source.analysis.matching.source_requirement_matcher_factory import SourceRequirementMatcherFactory
from source.analysis.matching.source_requirement_matches import SourceRequirementMatches
from source.analysis.relationships.source_reference_candidate_resolver import SourceReferenceCandidateResolver
from source.analysis.relationships.source_relationship_resolver import SourceRelationshipResolver
from source.analyze_source_input import AnalyzeSourceInput
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.text_analysis_source import TextAnalysisSource


"""
solid-name: TestSourceRequirementMatching
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies requirement candidates use recorded ownership and typed signatures while retaining uncertainty and original source evidence.
"""
class TestSourceRequirementMatching(unittest.TestCase):
    def setUp(self) -> None:
        self.analysis = SourceAnalysisOperationFactory().make()
        self.relationships = SourceRelationshipResolver(SourceReferenceCandidateResolver())
        self.matcher = SourceRequirementMatcherFactory().make()

    def match(self, *sources: str, relationship_index: int = 0) -> SourceRequirementMatches:
        inventory = self.relationships.resolve([
            self.analysis.execute(AnalyzeSourceInput(source=TextAnalysisSource(
                virtual_path=f"Source{index}.swift", text=code,
            )))
            for index, code in enumerate(sources)
        ])
        return self.matcher.match(inventory, inventory.relationships[relationship_index])

    def test_separate_extension_matches_without_including_unrelated_same_signature(self) -> None:
        result = self.match(
            "protocol Reading { func read(id: Int) -> String }",
            "struct Store: Reading {}",
            'extension Store { func read(id value: Int) -> String { "ok" } }',
            'struct Unrelated { func read(id: Int) -> String { "wrong owner" } }',
        )

        match = result.matches[0]
        self.assertEqual(match.status.value, "candidate")
        self.assertEqual(len(match.candidates), 1)
        self.assertEqual(match.candidates[0].owner.source_identity, result.inventory.analyses[2].source_identity)
        self.assertEqual(match.candidates[0].member.span, result.inventory.analyses[2].units[0].members[0].span)

    def test_overloads_preserve_external_labels_and_parameter_types(self) -> None:
        result = self.match(
            "protocol Reading { func read(id: Int); func read(id: String); func read(_ id: Int) }",
            "struct Store: Reading { func read(id value: String) {}; func read(_ value: Int) {}; func read(id renamed: Int) {} }",
        )

        self.assertEqual([item.status.value for item in result.matches], ["candidate"] * 3)
        self.assertEqual(
            [item.candidates[0].member.identity for item in result.matches],
            [result.inventory.analyses[1].units[0].members[index].identity for index in [2, 0, 1]],
        )

    def test_extension_declared_conformance_can_use_base_and_sibling_extension_members(self) -> None:
        result = self.match(
            "protocol Reading { func read(); func close() }",
            "struct Store { func read() {} }",
            "extension Store: Reading {}",
            "extension Store { func close() {} }",
            relationship_index=1,
        )

        self.assertEqual([item.status.value for item in result.matches], ["candidate", "candidate"])
        self.assertEqual(
            [item.candidates[0].owner.source_identity for item in result.matches],
            [result.inventory.analyses[1].source_identity, result.inventory.analyses[3].source_identity],
        )

    def test_protocol_extension_default_is_preserved_as_a_candidate(self) -> None:
        result = self.match(
            "protocol Reading { func read() }",
            "struct Store: Reading {}",
            "extension Reading { func read() {} }",
        )

        self.assertEqual(result.matches[0].status.value, "candidate")
        self.assertEqual(result.matches[0].candidates[0].owner.source_identity, result.inventory.analyses[2].source_identity)
        self.assertEqual(result.matches[0].candidates[0].relationships[0].reference.kind.value, "extension_target")

    def test_multiple_implementations_remain_ambiguous_without_selecting_dispatch(self) -> None:
        result = self.match(
            "protocol Reading { func read() }",
            "struct Store: Reading { func read() {} }",
            "extension Reading { func read() {} }",
        )

        self.assertEqual(result.matches[0].status.value, "ambiguous")
        self.assertEqual(len(result.matches[0].candidates), 2)

    def test_missing_member_is_unresolved_not_a_stub_or_compliance_result(self) -> None:
        result = self.match("protocol Reading { func read() }", "struct Store: Reading {}")

        self.assertEqual(result.matches[0].status.value, "unresolved")
        self.assertEqual(result.matches[0].candidates, [])
        self.assertIn("not established", result.matches[0].reason)

    def test_ambiguous_interface_owner_does_not_become_verified_through_matching(self) -> None:
        result = self.match(
            "protocol Reading { func read() }",
            "protocol Reading { func read() }",
            "struct Store: Reading { func read() {} }",
        )

        self.assertEqual([item.status.value for item in result.matches], ["ambiguous", "ambiguous"])
        self.assertEqual(len(result.matches[0].candidates), 1)
        self.assertNotEqual(result.matches[0].interface, result.matches[1].interface)

    def test_conditional_extension_preserves_candidate_but_remains_unresolved(self) -> None:
        result = self.match(
            "protocol Reading { func read() }",
            "struct Store: Reading {}",
            "extension Store where Self: Other { func read() {} }",
        )

        self.assertEqual(result.matches[0].status.value, "unresolved")
        self.assertEqual(len(result.matches[0].candidates), 1)
        self.assertTrue(result.matches[0].candidates[0].relationships[0].reference.constraints)

    def test_property_getter_accepts_stored_mutable_property(self) -> None:
        result = self.match(
            "protocol Reading { var count: Int { get } }",
            "struct Store: Reading { public var count: Int = 0 }",
        )

        self.assertEqual(result.matches[0].status.value, "candidate")
        self.assertEqual(result.matches[0].candidates[0].member.signature.accessors, ["get", "set"])

    def test_required_setter_does_not_match_read_only_or_restricted_setter(self) -> None:
        result = self.match(
            "protocol Reading { var count: Int { get set }; var size: Int { get set } }",
            "struct Store: Reading { let count: Int = 0; private(set) var size: Int = 0 }",
        )

        self.assertEqual([item.status.value for item in result.matches], ["unresolved", "unresolved"])
        self.assertEqual([item.candidates for item in result.matches], [[], []])

    def test_subscripts_match_by_callable_shape_and_accessor_requirements(self) -> None:
        result = self.match(
            "protocol Reading { subscript(index: Int) -> String { get } }",
            'struct Store: Reading { subscript(value: Int) -> String { "ok" }; subscript(value: String) -> String { value } }',
        )

        self.assertEqual(result.matches[0].status.value, "candidate")
        self.assertEqual(len(result.matches[0].candidates), 1)
        self.assertEqual(result.matches[0].candidates[0].member.signature.callable.parameters[0].type_tokens, ["Int"])

    def test_associated_type_requirement_is_retained_as_unresolved(self) -> None:
        result = self.match(
            "protocol Reading { associatedtype Item: Equatable }",
            "struct Store: Reading { typealias Item = Int }",
        )

        self.assertEqual(result.matches[0].requirement.kind.value, "associated_type")
        self.assertEqual(result.matches[0].status.value, "unresolved")
        self.assertEqual(result.matches[0].candidates, [])

    def test_generic_method_needs_semantic_constraint_resolution(self) -> None:
        result = self.match(
            "protocol Reading { func read<T: Equatable>(_ item: T) }",
            "struct Store: Reading { func read<T: Equatable>(_ item: T) {} }",
        )

        self.assertEqual(result.matches[0].status.value, "unresolved")
        self.assertEqual(result.matches[0].candidates, [])

    def test_static_and_instance_members_do_not_match(self) -> None:
        result = self.match(
            "protocol Reading { static func read() }",
            "struct Store: Reading { func read() {} }",
        )

        self.assertEqual(result.matches[0].status.value, "unresolved")
        self.assertEqual(result.matches[0].candidates, [])

    def test_visibility_is_retained_for_downstream_filtering_not_reclassified(self) -> None:
        result = self.match(
            "protocol Reading { func read() }",
            "struct Store: Reading { private func read() {} }",
        )

        self.assertEqual(result.matches[0].candidates[0].member.visibility.value, "private")
        self.assertEqual(result.inventory.verification, "unverified_candidates")

    def test_results_round_trip_with_relationships_and_member_evidence(self) -> None:
        result = self.match("protocol Reading { func read() }", "struct Store: Reading { func read() {} }")

        restored = SourceRequirementMatches.model_validate_json(result.model_dump_json())

        self.assertEqual(restored, result)

    def test_extension_target_cannot_be_used_as_conformance_request(self) -> None:
        with self.assertRaisesRegex(ValueError, "inherited"):
            self.match("struct Store {}", "extension Store {}")

    def test_ambiguous_extension_owner_preserves_possible_member_and_ambiguity(self) -> None:
        result = self.match(
            "protocol Reading { func read() }",
            "struct Store: Reading {}",
            "struct Store {}",
            "extension Store { func read() {} }",
        )

        self.assertEqual(result.matches[0].status.value, "ambiguous")
        self.assertEqual(len(result.matches[0].candidates), 1)
        self.assertEqual(len(result.matches[0].candidates[0].relationships[0].candidates), 2)

    def test_generic_owner_does_not_erase_relationship_uncertainty(self) -> None:
        result = self.match(
            "protocol Reading { func read() }",
            "struct Store<T>: Reading { func read() {} }",
        )

        self.assertEqual(result.matches[0].status.value, "unresolved")
        self.assertEqual(len(result.matches[0].candidates), 1)
        self.assertIn("generic", result.matches[0].reason)

    def test_inherited_protocol_requirement_is_not_fabricated_in_direct_inventory(self) -> None:
        result = self.match(
            "protocol Base { func read() }; protocol Reading: Base { func close() }",
            "struct Store: Reading { func close() {} }",
            relationship_index=1,
        )

        self.assertEqual([item.requirement.name for item in result.matches], ["close"])
        self.assertEqual(result.matches[0].status.value, "candidate")
        self.assertEqual(len(result.inventory.relationships), 2)

    def test_protocol_inheritance_does_not_turn_requirements_into_implementations(self) -> None:
        result = self.match(
            "protocol Reading { func read() }",
            "protocol OtherReading: Reading { func read() }",
        )

        self.assertEqual(result.matches[0].status.value, "unresolved")
        self.assertEqual(result.matches[0].candidates, [])

    def test_malformed_implementation_retains_partial_analysis_diagnostics(self) -> None:
        result = self.match(
            "protocol Reading { func read() }",
            "struct Store: Reading {}",
            "extension Store { func read() { let value = } }",
        )

        self.assertEqual(result.matches[0].status.value, "unresolved")
        self.assertEqual(result.inventory.analyses[2].decision.value, "partial")
        self.assertTrue(result.inventory.analyses[2].diagnostics)

    def test_unresolved_interface_is_not_reported_as_verified_empty_contract(self) -> None:
        result = self.match("struct Store: ExternalReading { func read() {} }")

        self.assertEqual(result.matches, [])
        self.assertEqual(result.relationship.status.value, "unresolved")
        self.assertEqual(result.inventory.verification, "unverified_candidates")

    def test_persisted_source_snapshot_can_be_rematched_without_source_analysis(self) -> None:
        original = self.match("protocol Reading { func read() }", "struct Store: Reading { func read() {} }")
        restored = SourceRequirementMatches.model_validate_json(original.model_dump_json())

        result = self.matcher.match(restored.inventory, restored.relationship)

        self.assertEqual(result, original)

    def test_relationship_from_different_snapshot_is_rejected(self) -> None:
        first = self.match("protocol Reading { func read() }", "struct Store: Reading { func read() {} }")
        other = self.match("protocol Writing { func write() }", "struct Store: Writing { func write() {} }")

        with self.assertRaisesRegex(ValueError, "recorded"):
            self.matcher.match(first.inventory, other.relationship)
