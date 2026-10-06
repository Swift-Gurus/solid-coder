"""Tests direct declaration-member facts through the source-analysis boundary."""

import tempfile
import unittest
from pathlib import Path

from source.analyze_source_input import AnalyzeSourceInput
from source.file_analysis_source import FileAnalysisSource
from source.source_analysis_decision import SourceAnalysisDecision
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.text_analysis_source import TextAnalysisSource


"""
solid-name: TestSourceMemberInventory
solid-category: unit-test
solid-spec: [SPEC-062]
solid-description: Verifies deterministic declaration-member identity, visibility, and source evidence for file and prospective buffer analysis.
"""
class TestSourceMemberInventory(unittest.TestCase):
    def setUp(self) -> None:
        self.operation = SourceAnalysisOperationFactory().make()

    def test_protocol_members_are_direct_ordered_and_distinguish_overloads(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Contract.swift",
            text=(
                "protocol Parent { func inherited() }\n"
                "protocol Contract: Parent {\n"
                "  associatedtype Item\n"
                "  var count: Int { get set }\n"
                "  func read(_ value: Int); func read(_ value: String)\n"
                "}\n"
            ),
        )))

        members = result.units[1].members
        self.assertEqual([member.name for member in members], ["Item", "count", "read", "read"])
        self.assertEqual(
            [member.kind.value for member in members],
            ["associated_type", "property", "method", "method"],
        )
        self.assertEqual([member.span.start for member in members], [3, 4, 5, 5])
        self.assertEqual(len({member.identity for member in members}), 4)

    def test_extension_defaults_and_explicit_access_are_preserved(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Extensions.swift",
            text=(
                "protocol Contract {}\n"
                "private extension Contract { func hidden() {} }\n"
                "fileprivate extension Contract { func fileOnly() {} }\n"
                "public extension Contract {\n"
                "  func published() {}\n"
                "  internal func local() {}\n"
                "  private func helper() {}\n"
                "}\n"
                "extension Contract {\n"
                "  fileprivate func restricted() {}\n"
                "  package func packageOnly() {}\n"
                "  func visible() {}\n"
                "}\n"
            ),
        )))

        members = [member for unit in result.units for member in unit.members]
        self.assertEqual(
            [member.visibility.value for member in members],
            ["private", "fileprivate", "public", "internal", "private", "fileprivate", "package", "internal"],
        )

    def test_private_setter_does_not_hide_property_or_duplicate_accessors(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="State.swift",
            text=(
                "public class State {\n"
                "  public private(set) var count = 0\n"
                "  var title: String { get { \"Hi\" } set {} }\n"
                "}\n"
            ),
        )))

        members = result.units[0].members
        self.assertEqual([member.name for member in members], ["count", "title"])
        self.assertEqual([member.visibility.value for member in members], ["public", "internal"])

    def test_protocol_access_and_nominal_owner_restrictions_are_preserved(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Access.swift",
            text=(
                "public protocol Published { func read() }\n"
                "private class Hidden { func read() {} }\n"
                "fileprivate struct Local { func read() {} }\n"
                "open class Document { open func read() {}; func write() {} }\n"
            ),
        )))

        members = [member for unit in result.units for member in unit.members]
        self.assertEqual(
            [member.visibility.value for member in members],
            ["public", "private", "fileprivate", "open", "internal"],
        )

    def test_property_evidence_covers_multiline_binding_without_extra_members(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Computed.swift",
            text=(
                "struct Computed {\n"
                "  var value: Int {\n"
                "    get {\n"
                "      42\n"
                "    }\n"
                "  }\n"
                "}\n"
            ),
        )))

        members = result.units[0].members
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].name, "value")
        self.assertEqual(members[0].span.start, 2)
        self.assertEqual(members[0].span.end, 6)

    def test_lifecycle_and_subscript_are_distinct_without_nested_method_leakage(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Container.swift",
            text=(
                "class Container {\n"
                "  init() {}\n"
                "  deinit {}\n"
                "  subscript(index: Int) -> Int { index }\n"
                "  struct Nested { func hidden() {} }\n"
                "  func outer() { func local() {} }\n"
                "}\n"
            ),
        )))

        members = result.units[0].members
        self.assertEqual(
            [member.kind.value for member in members],
            ["initializer", "deinitializer", "subscript", "method"],
        )
        self.assertEqual([member.name for member in members], ["init", "deinit", "subscript", "outer"])

    def test_equivalent_file_and_unwritten_buffer_preserve_unicode_line_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Unicode.swift"
            text = '// café 😀\nprotocol Café {\n  func télécharger()\n}\n'
            buffer_result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
                text=text, virtual_path=str(path),
            )))
            self.assertFalse(path.exists())
            path.write_text(text, encoding="utf-8")
            file_result = self.operation.execute(AnalyzeSourceInput(source=FileAnalysisSource(path=path)))

        self.assertEqual(file_result, buffer_result)
        member = file_result.units[0].members[0]
        self.assertEqual(member.name, "télécharger")
        self.assertEqual(member.span.start, 3)
        self.assertEqual(member.span.end, 3)

    def test_partial_and_unsupported_analysis_keep_explicit_limitations(self) -> None:
        partial = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            text="protocol Complete { func read() }\nclass Broken {\n",
            virtual_path="Partial.swift",
        )))
        unsupported = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            text="class Example: pass\n", virtual_path="example.py",
        )))

        self.assertEqual(partial.decision, SourceAnalysisDecision.PARTIAL)
        self.assertEqual([member.name for member in partial.units[0].members], ["read"])
        self.assertEqual(unsupported.decision, SourceAnalysisDecision.WHOLE_FILE_UNSUPPORTED)
        self.assertEqual(unsupported.units[0].members, [])
