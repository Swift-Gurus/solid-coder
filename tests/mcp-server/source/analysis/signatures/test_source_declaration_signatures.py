"""Integration coverage for declaration header facts used in relationship analysis."""

import unittest

from source.analyze_source_input import AnalyzeSourceInput
from source.source_analysis import SourceAnalysis
from source.source_analysis_decision import SourceAnalysisDecision
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.text_analysis_source import TextAnalysisSource

"""
solid-name: TestSourceDeclarationSignatures
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies source analysis preserves declared inheritance, extension targets, constraints, and incomplete syntax without asserting resolved relationships.
"""


class TestSourceDeclarationSignatures(unittest.TestCase):
    def setUp(self) -> None:
        self.operation = SourceAnalysisOperationFactory().make()

    def test_inherited_names_remain_ordered_qualified_and_evidenced(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="struct Store: Networking.Loading, Persisting {}",
                )
            )
        )

        signature = result.units[0].signature
        self.assertEqual(signature.kind, "declaration")
        self.assertEqual(signature.name.tokens, ["Store"])
        self.assertEqual(
            [base.tokens for base in signature.inherited_types],
            [["Networking", ".", "Loading"], ["Persisting"]],
        )
        self.assertEqual(
            [base.span.start for base in signature.inherited_types], [1, 1]
        )

    def test_protocol_inheritance_does_not_invent_inherited_members(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="protocol Loading { func load() }\nprotocol Store: Loading { func save() }",
                )
            )
        )

        unit = result.units[1]
        self.assertEqual(unit.kind.value, "protocol")
        self.assertEqual(unit.signature.inherited_types[0].tokens, ["Loading"])
        self.assertEqual([member.name for member in unit.members], ["save"])

    def test_qualified_extension_target_and_constraints_are_preserved(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="extension Catalog.Store where Item: Equatable { func load() {} }",
                )
            )
        )

        unit = result.units[0]
        self.assertEqual(unit.kind.value, "extension")
        self.assertEqual(unit.signature.name.tokens, ["Catalog", ".", "Store"])
        self.assertEqual(
            unit.signature.constraints, ["where", "Item", ":", "Equatable"]
        )
        self.assertEqual([member.name for member in unit.members], ["load"])

    def test_extension_conformance_is_retained_separately_from_target(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="extension Store: Loading, Persisting {}",
                )
            )
        )

        signature = result.units[0].signature
        self.assertEqual(signature.name.tokens, ["Store"])
        self.assertEqual(
            [base.tokens for base in signature.inherited_types],
            [["Loading"], ["Persisting"]],
        )

    def test_generic_parameters_inherited_arguments_and_constraints_are_retained(
        self,
    ) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="class Store<Item: Hashable>: Base<Item>, Loading where Item: Sendable {}",
                )
            )
        )

        signature = result.units[0].signature
        self.assertEqual(
            signature.generic_parameters, ["<", "Item", ":", "Hashable", ">"]
        )
        self.assertEqual(
            [base.tokens for base in signature.inherited_types],
            [["Base", "<", "Item", ">"], ["Loading"]],
        )
        self.assertEqual(signature.constraints, ["where", "Item", ":", "Sendable"])

    def test_attributes_and_access_remain_facts_not_exception_decisions(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="@objc public protocol Loading { func load() }",
                )
            )
        )

        self.assertEqual(result.units[0].signature.modifiers, ["@", "objc", "public"])
        self.assertEqual(result.units[0].signature.inherited_types, [])

    def test_nested_declaration_does_not_pollute_parent_inheritance(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="struct Outer { struct Store: Loading {} }",
                )
            )
        )

        self.assertEqual(result.units[0].signature.name.tokens, ["Outer"])
        self.assertEqual(result.units[0].signature.inherited_types, [])

    def test_comments_do_not_change_declared_type_tokens(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="struct Store: Networking /* module */ . Loading {}",
                )
            )
        )

        self.assertEqual(
            result.units[0].signature.inherited_types[0].tokens,
            ["Networking", ".", "Loading"],
        )
        self.assertEqual(result.decision, SourceAnalysisDecision.PARSED)

    def test_incomplete_declaration_cannot_claim_complete_header_facts(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="struct Store: Loading { func load() { let result = } }",
                )
            )
        )

        self.assertEqual(result.decision, SourceAnalysisDecision.PARTIAL)
        self.assertEqual(result.units[0].signature.kind, "unresolved")
        self.assertTrue(result.units[0].signature.reason)

    def test_free_function_is_not_published_as_nominal_declaration(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="func load() {}",
                )
            )
        )

        self.assertEqual(result.units[0].signature.kind, "unresolved")
        self.assertTrue(result.units[0].signature.reason)

    def test_declaration_facts_survive_analysis_json_round_trip(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="extension Store: Loading where Item: Equatable {}",
                )
            )
        )

        restored = SourceAnalysis.model_validate_json(result.model_dump_json())

        self.assertEqual(restored.units[0].signature.kind, "declaration")
        self.assertEqual(restored.units[0].signature, result.units[0].signature)
