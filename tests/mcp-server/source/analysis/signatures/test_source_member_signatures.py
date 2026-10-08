"""Exercises typed member signatures through the real source-analysis operation."""

import unittest

from source.analyze_source_input import AnalyzeSourceInput
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.source_analysis import SourceAnalysis
from source.source_analysis_decision import SourceAnalysisDecision
from source.text_analysis_source import TextAnalysisSource


"""
solid-name: TestSourceMemberSignatures
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies source analysis preserves comparable member signature facts without confusing syntax with resolved conformance.
"""
class TestSourceMemberSignatures(unittest.TestCase):
    def setUp(self) -> None:
        self.operation = SourceAnalysisOperationFactory().make()

    def test_internal_parameter_names_do_not_change_callable_signature(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift",
            text="protocol Store { func load(id: Int) -> String }\n"
                 "extension Store { func load(id value: Int) -> String { String(value) } }",
        )))

        requirement = result.units[0].members[0].signature
        implementation = result.units[1].members[0].signature
        self.assertEqual(requirement.kind, "callable")
        self.assertEqual(requirement.parameters[0].external_label, "id")
        self.assertEqual(requirement, implementation)

    def test_overloads_preserve_labels_and_types(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift",
            text="protocol Store {\n func load(id: Int)\n func load(id: String)\n"
                 " func load(_ id: Int)\n}",
        )))

        signatures = [member.signature for member in result.units[0].members]
        self.assertEqual([signature.parameters[0].external_label for signature in signatures], ["id", "id", "_"])
        self.assertEqual([signature.parameters[0].type_tokens for signature in signatures], [["Int"], ["String"], ["Int"]])
        self.assertNotEqual(signatures[0], signatures[1])
        self.assertNotEqual(signatures[0], signatures[2])

    def test_formatting_comments_and_default_values_do_not_change_signature(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift",
            text="struct Store {\n func load(id: [String: Int?] = [:]) -> [String: Int?] { id }\n"
                 " func load(id renamed: [ String /* type */ : Int? ]) -> [ String : Int? ] { renamed }\n}",
        )))

        first, second = result.units[0].members
        self.assertEqual(first.signature, second.signature)
        self.assertEqual(first.signature.return_type, ["[", "String", ":", "Int", "?", "]"])

    def test_generic_constraints_and_effects_remain_available(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift",
            text="protocol Store { static func load<T: Hashable>(_ value: inout T) async throws -> T where T: Sendable }",
        )))

        signature = result.units[0].members[0].signature
        self.assertEqual(signature.generic_parameters, ["<", "T", ":", "Hashable", ">"])
        self.assertEqual(signature.constraints, ["where", "T", ":", "Sendable"])
        self.assertEqual(signature.modifiers, ["static", "async", "throws"])
        self.assertEqual(signature.parameters[0].type_tokens, ["inout", "T"])

    def test_property_requirements_preserve_type_and_accessors(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift",
            text="protocol Store { var item: Item { get set }; var count: Int { get } }",
        )))

        item, count = result.units[0].members
        self.assertEqual(item.signature.kind, "value")
        self.assertEqual(item.signature.value_type, ["Item"])
        self.assertEqual(item.signature.accessors, ["get", "set"])
        self.assertEqual(count.signature.accessors, ["get"])

    def test_each_property_binding_uses_its_own_type(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift",
            text='struct Store { var count: Int = 1, label: String = "one" }',
        )))

        count, label = result.units[0].members
        self.assertEqual(count.signature.value_type, ["Int"])
        self.assertEqual(label.signature.value_type, ["String"])

    def test_associated_type_bounds_and_constraints_are_preserved(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift",
            text="protocol Store { associatedtype Item: Equatable where Item: Sendable }",
        )))

        signature = result.units[0].members[0].signature
        self.assertEqual(signature.kind, "associated_type")
        self.assertEqual(signature.bounds, ["Equatable"])
        self.assertEqual(signature.constraints, ["where", "Item", ":", "Sendable"])

    def test_inferred_property_type_is_explicitly_unresolved(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift", text="struct Store { var count = 1 }",
        )))

        signature = result.units[0].members[0].signature
        self.assertEqual(signature.kind, "unresolved")
        self.assertIn("type", signature.reason.lower())

    def test_signature_variants_survive_analysis_serialization(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift",
            text="protocol Store { func load(id: Int); var value: Int { get }; associatedtype Item }",
        )))

        restored = SourceAnalysis.model_validate_json(result.model_dump_json())

        self.assertEqual(restored, result)
        self.assertEqual(restored.units[0].members[0].signature.parameters[0].external_label, "id")

    def test_private_setter_restriction_is_retained(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift", text="struct Store { public private(set) var count: Int = 0 }",
        )))

        signature = result.units[0].members[0].signature
        self.assertEqual(signature.accessors, ["get", "set"])
        self.assertEqual(signature.modifiers, ["public", "private", "(", "set", ")"])

    def test_comment_inside_type_annotation_is_not_an_inferred_type(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift", text="struct Store { var count: /* units */ Int = 0 }",
        )))

        self.assertEqual(result.units[0].members[0].signature.value_type, ["Int"])

    def test_unsupported_comment_placement_reports_partial_analysis(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift", text="struct Store { var count /* units */ : Int = 0 }",
        )))

        self.assertEqual(result.decision, SourceAnalysisDecision.PARTIAL)
        self.assertTrue(result.diagnostics)

    def test_empty_accessor_shape_is_explicitly_unresolved(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift", text="struct Store { var count: Int {} }",
        )))

        signature = result.units[0].members[0].signature
        self.assertEqual(signature.kind, "unresolved")
        self.assertIn("accessor", signature.reason.lower())

    def test_incomplete_declaration_has_unresolved_signature_and_diagnostic(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift", text="struct Store { func load(id: Int) { let result = } }",
        )))

        self.assertEqual(result.units[0].members[0].signature.kind, "unresolved")
        self.assertTrue(result.diagnostics)

    def test_subscript_signature_preserves_callable_and_accessor_facts(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift", text="protocol Store { subscript(index: Int) -> String { get } }",
        )))

        signature = result.units[0].members[0].signature
        self.assertEqual(signature.kind, "subscript")
        self.assertEqual(signature.callable.parameters[0].external_label, "_")
        self.assertEqual(signature.callable.return_type, ["String"])
        self.assertEqual(signature.accessors, ["get"])

    def test_destructured_binding_does_not_copy_whole_tuple_type_to_each_member(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift", text='struct Store { var (count, label): (Int, String) = (1, "one") }',
        )))

        self.assertEqual([member.signature.kind for member in result.units[0].members], ["unresolved", "unresolved"])

    def test_typed_throws_preserves_the_declared_error_type(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift", text="protocol Store { func load() throws(StoreError) -> Int }",
        )))

        self.assertEqual(result.units[0].members[0].signature.modifiers, ["throws", "(", "StoreError", ")"])

    def test_variadic_parameter_preserves_its_variadic_marker(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift", text="protocol Store { func load(values: Int...) }",
        )))

        self.assertEqual(result.units[0].members[0].signature.parameters[0].type_tokens, ["Int", "..."])

    def test_failable_initializer_preserves_its_failure_marker(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift", text="struct Store { init?(id: Int) {} }",
        )))

        self.assertEqual(result.units[0].members[0].signature.modifiers, ["?"])

    def test_property_getter_retains_async_and_throwing_effects(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift", text="protocol Store { var value: Int { get async throws } }",
        )))

        self.assertEqual(result.units[0].members[0].signature.accessors, ["get", "async", "throws"])

    def test_property_type_attributes_are_preserved(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift", text="protocol Store { var callback: @Sendable (Int) -> Void { get } }",
        )))

        self.assertEqual(result.units[0].members[0].signature.value_type, ["@", "Sendable", "(", "Int", ")", "->", "Void"])

    def test_return_type_attributes_are_preserved(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Store.swift", text="protocol Store { func callback() -> @Sendable (Int) -> Void }",
        )))

        self.assertEqual(result.units[0].members[0].signature.return_type, ["@", "Sendable", "(", "Int", ")", "->", "Void"])
