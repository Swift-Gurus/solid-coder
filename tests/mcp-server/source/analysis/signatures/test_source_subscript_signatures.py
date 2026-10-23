"""Integration coverage for subscript signatures from source analysis."""

import unittest

from source.analyze_source_input import AnalyzeSourceInput
from source.source_analysis import SourceAnalysis
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.text_analysis_source import TextAnalysisSource

"""
solid-name: TestSourceSubscriptSignatures
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies subscript parameter labels, result types, accessors, generic constraints, and unresolved syntax through the shared source-analysis operation.
"""


class TestSourceSubscriptSignatures(unittest.TestCase):
    def setUp(self) -> None:
        self.operation = SourceAnalysisOperationFactory().make()

    def test_requirement_preserves_unlabeled_index_type_result_and_accessors(
        self,
    ) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="protocol Store { subscript(index: Int) -> String { get set } }",
                )
            )
        )

        signature = result.units[0].members[0].signature
        self.assertEqual(signature.kind, "subscript")
        self.assertEqual(signature.callable.parameters[0].external_label, "_")
        self.assertEqual(signature.callable.parameters[0].type_tokens, ["Int"])
        self.assertEqual(signature.callable.return_type, ["String"])
        self.assertEqual(signature.accessors, ["get", "set"])

    def test_explicit_argument_label_is_not_replaced_with_internal_name(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="protocol Store { subscript(at index: Int) -> String { get } }",
                )
            )
        )

        self.assertEqual(
            result.units[0].members[0].signature.callable.parameters[0].external_label,
            "at",
        )

    def test_shorthand_body_is_read_only(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text='struct Store { subscript(index: Int) -> String { "value" } }',
                )
            )
        )

        self.assertEqual(result.units[0].members[0].signature.accessors, ["get"])

    def test_internal_renaming_and_bodies_do_not_change_subscript_signature(
        self,
    ) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="protocol Store { subscript(index: Int) -> String { get } }\n"
                    'extension Store { subscript(position: Int) -> String { "value" } }',
                )
            )
        )

        self.assertEqual(result.units[0].members[0].signature.kind, "subscript")
        self.assertEqual(
            result.units[0].members[0].signature, result.units[1].members[0].signature
        )

    def test_overloads_retain_distinct_index_types(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="protocol Store {\n subscript(index: Int) -> String { get }\n"
                    " subscript(key: String) -> String { get }\n}",
                )
            )
        )

        first, second = result.units[0].members
        self.assertEqual(first.signature.callable.parameters[0].type_tokens, ["Int"])
        self.assertEqual(
            second.signature.callable.parameters[0].type_tokens, ["String"]
        )
        self.assertNotEqual(first.signature, second.signature)

    def test_generic_constraints_and_declaration_modifiers_are_preserved(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="struct Store { public subscript<T: Hashable>(key: T) -> T where T: Sendable { key } }",
                )
            )
        )

        signature = result.units[0].members[0].signature.callable
        self.assertEqual(signature.generic_parameters, ["<", "T", ":", "Hashable", ">"])
        self.assertEqual(signature.constraints, ["where", "T", ":", "Sendable"])
        self.assertEqual(signature.modifiers, ["public"])

    def test_effectful_getter_retains_async_and_throws(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="protocol Store { subscript(index: Int) -> String { get async throws } }",
                )
            )
        )

        self.assertEqual(
            result.units[0].members[0].signature.accessors, ["get", "async", "throws"]
        )

    def test_empty_accessor_block_remains_unresolved(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="struct Store { subscript(index: Int) -> String {} }",
                )
            )
        )

        signature = result.units[0].members[0].signature
        self.assertEqual(signature.kind, "unresolved")
        self.assertIn("accessor", signature.reason.lower())

    def test_incomplete_subscript_keeps_diagnostics_and_unresolved_signature(
        self,
    ) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="struct Store { subscript(index: Int) -> String { let result = } }",
                )
            )
        )

        self.assertEqual(result.units[0].members[0].signature.kind, "unresolved")
        self.assertTrue(result.diagnostics)

    def test_subscript_signature_survives_analysis_json_round_trip(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Store.swift",
                    text="protocol Store { subscript(index: Int) -> String { get } }",
                )
            )
        )

        restored = SourceAnalysis.model_validate_json(result.model_dump_json())

        self.assertEqual(restored.units[0].members[0].signature.kind, "subscript")
        self.assertEqual(
            restored.units[0].members[0].signature, result.units[0].members[0].signature
        )
