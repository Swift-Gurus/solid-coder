import unittest

from source.analysis.relationships.source_reference_candidate_resolver import (
    SourceReferenceCandidateResolver,
)
from source.analysis.relationships.source_relationship_inventory import (
    SourceRelationshipInventory,
)
from source.analysis.relationships.source_relationship_resolver import (
    SourceRelationshipResolver,
)
from source.analyze_source_input import AnalyzeSourceInput
from source.source_analysis import SourceAnalysis
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.text_analysis_source import TextAnalysisSource

"""
solid-name: TestSourceRelationshipResolution
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies bounded declaration links retain source ownership, ambiguity, constraints, and analysis limitations without claiming verified conformance.
"""


class TestSourceRelationshipResolution(unittest.TestCase):
    def setUp(self) -> None:
        self.analysis = SourceAnalysisOperationFactory().make()
        self.resolver = SourceRelationshipResolver(SourceReferenceCandidateResolver())

    def analyze(self, path: str, code: str) -> SourceAnalysis:
        return self.analysis.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path=path,
                    text=code,
                )
            )
        )

    def test_declared_inheritance_and_separate_extension_produce_bounded_links(
        self,
    ) -> None:
        interface = self.analyze("Reading.swift", "protocol Reading { func read() }")
        conformer = self.analyze("Store.swift", "struct Store: Reading {}")
        extension = self.analyze(
            "Store+Reading.swift", "extension Store { func read() {} }"
        )

        result = self.resolver.resolve([interface, conformer, extension])

        self.assertEqual(result.scope, "supplied_top_level_sources")
        self.assertEqual(result.verification, "unverified_candidates")
        self.assertEqual(result.analyses, [interface, conformer, extension])
        self.assertEqual(len(result.relationships), 2)
        inherited, extended = result.relationships
        self.assertEqual(inherited.reference.kind.value, "inherited_type")
        self.assertEqual(
            inherited.reference.owner.source_identity, conformer.source_identity
        )
        self.assertEqual(
            inherited.reference.owner.unit_identity, conformer.units[0].identity
        )
        self.assertEqual(inherited.status.value, "candidate")
        self.assertEqual(
            inherited.candidates[0].source_identity, interface.source_identity
        )
        self.assertEqual(
            inherited.candidates[0].unit_identity, interface.units[0].identity
        )
        self.assertEqual(extended.reference.kind.value, "extension_target")
        self.assertEqual(
            extended.candidates[0].source_identity, conformer.source_identity
        )
        self.assertEqual(
            extended.candidates[0].unit_identity, conformer.units[0].identity
        )
        self.assertEqual(
            inherited.reference.target.span,
            conformer.units[0].signature.inherited_types[0].span,
        )

    def test_identical_members_do_not_create_a_relationship(self) -> None:
        interface = self.analyze("Reading.swift", "protocol Reading { func read() }")
        unrelated = self.analyze(
            "Unrelated.swift", "struct Unrelated { func read() {} }"
        )

        result = self.resolver.resolve([interface, unrelated])

        self.assertEqual(result.relationships, [])
        self.assertEqual(
            result.analyses[1].units[0].members[0].signature,
            interface.units[0].members[0].signature,
        )

    def test_extension_conformance_keeps_target_and_inheritance_separate(self) -> None:
        interface = self.analyze("Reading.swift", "protocol Reading {}")
        owner = self.analyze("Store.swift", "struct Store {}")
        extension = self.analyze("Store+Reading.swift", "extension Store: Reading {}")

        result = self.resolver.resolve([interface, owner, extension])

        self.assertEqual(
            [item.reference.kind.value for item in result.relationships],
            ["extension_target", "inherited_type"],
        )
        self.assertEqual(
            [item.reference.target.tokens for item in result.relationships],
            [["Store"], ["Reading"]],
        )
        self.assertEqual(
            [item.candidates[0].source_identity for item in result.relationships],
            [owner.source_identity, interface.source_identity],
        )

    def test_declaration_matching_preserves_identifier_case(self) -> None:
        interface = self.analyze("Reading.swift", "protocol Reading {}")
        owner = self.analyze("Store.swift", "struct Store: reading {}")

        relationship = self.resolver.resolve([interface, owner]).relationships[0]

        self.assertEqual(relationship.status.value, "unresolved")
        self.assertEqual(relationship.candidates, [])

    def test_duplicate_names_remain_ambiguous_with_all_candidate_identities(
        self,
    ) -> None:
        first = self.analyze("First/Reading.swift", "protocol Reading {}")
        second = self.analyze("Second/Reading.swift", "protocol Reading {}")
        owner = self.analyze("Store.swift", "struct Store: Reading {}")

        relationship = self.resolver.resolve([first, second, owner]).relationships[0]

        self.assertEqual(relationship.status.value, "ambiguous")
        self.assertEqual(
            [item.source_identity for item in relationship.candidates],
            [first.source_identity, second.source_identity],
        )
        self.assertIn("multiple", relationship.reason.lower())

    def test_missing_declaration_remains_unresolved_instead_of_proving_absence(
        self,
    ) -> None:
        owner = self.analyze("Store.swift", "struct Store: Reading {}")

        relationship = self.resolver.resolve([owner]).relationships[0]

        self.assertEqual(relationship.status.value, "unresolved")
        self.assertEqual(relationship.candidates, [])
        self.assertEqual(relationship.reference.target.tokens, ["Reading"])
        self.assertIn("supplied", relationship.reason.lower())

    def test_qualified_reference_does_not_guess_from_its_last_name(self) -> None:
        interface = self.analyze("Reading.swift", "protocol Reading {}")
        owner = self.analyze("Store.swift", "struct Store: Other.Reading {}")

        relationship = self.resolver.resolve([interface, owner]).relationships[0]

        self.assertEqual(relationship.status.value, "unresolved")
        self.assertEqual(relationship.candidates, [])
        self.assertEqual(
            relationship.reference.target.tokens, ["Other", ".", "Reading"]
        )
        self.assertIn("semantic", relationship.reason.lower())

    def test_conditional_extension_preserves_possible_owner_without_claiming_applicability(
        self,
    ) -> None:
        owner = self.analyze("Store.swift", "struct Store<T> {}")
        extension = self.analyze(
            "Store+Reading.swift", "extension Store where T: Reading { func read() {} }"
        )

        relationship = self.resolver.resolve([owner, extension]).relationships[0]

        self.assertEqual(relationship.status.value, "unresolved")
        self.assertEqual(
            relationship.candidates[0].unit_identity, owner.units[0].identity
        )
        self.assertEqual(
            relationship.reference.constraints, ["where", "T", ":", "Reading"]
        )
        self.assertIn("semantic", relationship.reason.lower())

    def test_generic_owner_keeps_its_parameters_and_unresolved_relationship(
        self,
    ) -> None:
        interface = self.analyze("Reading.swift", "protocol Reading {}")
        owner = self.analyze("Store.swift", "struct Store<T>: Reading {}")

        relationship = self.resolver.resolve([interface, owner]).relationships[0]

        self.assertEqual(relationship.status.value, "unresolved")
        self.assertEqual(relationship.reference.generic_parameters, ["<", "T", ">"])
        self.assertEqual(len(relationship.candidates), 1)

    def test_generic_target_needs_semantic_resolution_even_without_extension_constraints(
        self,
    ) -> None:
        owner = self.analyze("Store.swift", "struct Store<T> {}")
        extension = self.analyze("Store+Reading.swift", "extension Store {}")

        relationship = self.resolver.resolve([owner, extension]).relationships[0]

        self.assertEqual(relationship.status.value, "unresolved")
        self.assertEqual(relationship.reference.constraints, [])
        self.assertEqual(len(relationship.candidates), 1)

    def test_declared_inheritance_does_not_infer_transitive_conformance(self) -> None:
        analysis = self.analyze(
            "Store.swift",
            "protocol Reading {}\nclass Base: Reading {}\nclass Store: Base {}",
        )

        result = self.resolver.resolve([analysis])

        self.assertEqual(len(result.relationships), 2)
        self.assertEqual(
            [item.reference.target.tokens for item in result.relationships],
            [["Reading"], ["Base"]],
        )
        self.assertEqual(
            result.relationships[1].candidates[0].unit_identity,
            analysis.units[1].identity,
        )

    def test_partial_and_unsupported_analyses_keep_their_diagnostics_in_the_scope(
        self,
    ) -> None:
        partial = self.analyze("Broken.swift", "struct Broken { let value = }")
        unsupported = self.analyze("Notes.md", "Missing declaration source")

        result = self.resolver.resolve([partial, unsupported])

        self.assertTrue(result.analyses[0].diagnostics)
        self.assertEqual(result.analyses[0].decision.value, "partial")
        self.assertEqual(result.analyses[1].decision.value, "whole_file_unsupported")
        self.assertEqual(result.relationships, [])

    def test_analysis_and_relationships_survive_json_round_trip(self) -> None:
        analysis = self.analyze(
            "Store.swift", "protocol Reading {}\nstruct Store: Reading {}"
        )
        result = self.resolver.resolve([analysis])

        restored = SourceRelationshipInventory.model_validate_json(
            result.model_dump_json()
        )

        self.assertEqual(restored, result)
        self.assertEqual(restored.relationships[0].status.value, "candidate")

    def test_empty_scope_does_not_claim_repository_completeness(self) -> None:
        result = self.resolver.resolve([])

        self.assertEqual(result.analyses, [])
        self.assertEqual(result.relationships, [])
        self.assertEqual(result.scope, "supplied_top_level_sources")
        self.assertEqual(result.verification, "unverified_candidates")

    def test_conflicting_snapshots_for_one_source_are_rejected(self) -> None:
        first = self.analyze("Store.swift", "struct Store {}")
        second = self.analyze("Store.swift", "struct Store: Reading {}")

        with self.assertRaisesRegex(ValueError, "source identity"):
            self.resolver.resolve([first, second])
