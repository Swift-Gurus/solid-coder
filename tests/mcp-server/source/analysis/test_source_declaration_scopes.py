"""Exercises lexical declaration inventory through the real source operation."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from git_working_tree_fixture import GitWorkingTreeFixture
from harness.project_context import ProjectDirectory
from source.analysis.tree_sitter_syntax_parser import TreeSitterSyntaxParser
from source.analyze_source_input import AnalyzeSourceInput
from source.file_analysis_source import FileAnalysisSource
from source.source_analysis import SourceAnalysis
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.text_analysis_source import TextAnalysisSource

"""
solid-name: TestSourceDeclarationScopes
solid-category: unit-test
solid-spec: [SPEC-066]
solid-description: Checks structural declaration scope, modifiers, stable identities, and prospective-source analysis without changing top-level review units.
"""


class TestSourceDeclarationScopes(unittest.TestCase):
    def setUp(self) -> None:
        self.operation = SourceAnalysisOperationFactory().make()

    def analyze(self, source: str, path: str = "Example.swift"):
        return self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(virtual_path=path, text=source),
            )
        )

    def test_local_and_nested_types_have_distinct_enclosing_scopes(self) -> None:
        source = """struct Outer {
    static func make() {
        if true { struct Local {} }
        let work = { struct InClosure {}; return 1 }
    }
    struct Nested {}
}
func free() { enum LocalEnum { case one } }
"""
        result = self.analyze(source)

        self.assertEqual([unit.name for unit in result.units], ["Outer", "free"])
        self.assertEqual(
            [entry.unit.name for entry in result.declarations],
            ["Outer", "make", "Local", "InClosure", "Nested", "free", "LocalEnum"],
        )
        self.assertEqual(
            [
                [scope.kind.value for scope in entry.scopes]
                for entry in result.declarations
            ],
            [
                [],
                ["type"],
                ["type", "callable"],
                ["type", "callable", "closure"],
                ["type"],
                [],
                ["callable"],
            ],
        )
        self.assertEqual(result.declarations[1].modifiers, ["static"])
        self.assertEqual(result.declarations[2].scopes[-1].name, "make")
        self.assertEqual(result.declarations[2].unit.span.start, 3)

    def test_initializers_and_accessors_are_callable_scopes(self) -> None:
        result = self.analyze("""struct Outer {
    init() { struct DuringInit {} }
    var value: Int { struct InGetter {}; return 1 }
    var other: Int { get { struct ExplicitGetter {}; return 2 } }
    deinit { struct DuringDeinit {} }
}
""")

        local = [entry for entry in result.declarations if entry.unit.name != "Outer"]
        self.assertEqual(
            [entry.unit.name for entry in local],
            ["DuringInit", "InGetter", "ExplicitGetter", "DuringDeinit"],
        )
        self.assertTrue(
            all(
                any(scope.kind.value == "callable" for scope in entry.scopes)
                for entry in local
            )
        )

    def test_same_line_overloads_and_local_names_keep_unique_identities(self) -> None:
        source = "func f(_ x: Int) { struct Local {} }; func f(_ x: String) { struct Local {} }"
        first = self.analyze(source)
        second = self.analyze(source)

        identities = [entry.identity for entry in first.declarations]
        self.assertEqual(len(identities), 4)
        self.assertEqual(len(set(identities)), 4)
        self.assertEqual(identities, [entry.identity for entry in second.declarations])

    def test_comments_literals_and_closures_are_not_type_declarations(self) -> None:
        result = self.analyze("""// struct Fake {}
struct Real {
    let text = "class Fake {}"
    let work = { 1 }
}
""")

        self.assertEqual([entry.unit.name for entry in result.declarations], ["Real"])

    def test_protocol_methods_and_class_modifiers_are_preserved(self) -> None:
        result = self.analyze(
            "protocol P { static func make() }\nclass C { class func make() {} }"
        )

        methods = [
            entry
            for entry in result.declarations
            if entry.unit.kind.value == "function"
        ]
        self.assertEqual(len(methods), 2)
        self.assertEqual(
            [entry.modifiers for entry in methods], [["static"], ["class"]]
        )
        self.assertEqual([entry.scopes[-1].name for entry in methods], ["P", "C"])

    def test_inventory_reuses_one_syntax_parse(self) -> None:
        with patch.object(
            TreeSitterSyntaxParser,
            "parse",
            autospec=True,
            side_effect=TreeSitterSyntaxParser.parse,
        ) as parse:
            result = self.analyze("func run() { struct Local {} }")

        self.assertEqual(parse.call_count, 1)
        self.assertEqual(len(result.declarations), 2)

    def test_prospective_buffer_does_not_read_or_write_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Missing.swift"
            result = self.analyze("func run() { struct Local {} }", str(path))
            self.assertFalse(path.exists())
            self.assertEqual(
                [entry.unit.name for entry in result.declarations], ["run", "Local"]
            )

    def test_unsupported_language_has_no_invented_declaration_inventory(self) -> None:
        result = self.analyze("class Example: pass", "Example.py")

        self.assertEqual(result.decision.value, "whole_file_unsupported")
        self.assertEqual(result.declarations, [])

    def test_file_and_buffer_share_facts_but_stale_file_is_not_read(self) -> None:
        source = "struct Outer { static func make() { struct Local {} } }"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            GitWorkingTreeFixture(root).initialize()
            self.operation = SourceAnalysisOperationFactory().make(
                ProjectDirectory(path=root)
            )
            path = root / "Example.swift"
            path.write_text(source, encoding="utf-8")
            on_disk = self.operation.execute(
                AnalyzeSourceInput(source=FileAnalysisSource(path=path))
            )
            in_memory = self.analyze(source, str(path))
            self.assertEqual(on_disk.declarations, in_memory.declarations)

            path.write_text("struct Stale {}", encoding="utf-8")
            prospective = self.analyze(source, str(path))
            self.assertEqual(prospective.declarations, in_memory.declarations)
            self.assertEqual(path.read_text(encoding="utf-8"), "struct Stale {}")

    def test_scope_inventory_survives_typed_serialization(self) -> None:
        original = self.analyze("func run() { struct Local {} }")

        restored = SourceAnalysis.model_validate_json(original.model_dump_json())

        self.assertEqual(restored, original)
        self.assertEqual(restored.declarations[1].scopes[0].kind.value, "callable")

    def test_partial_syntax_keeps_diagnostics_instead_of_claiming_completeness(
        self,
    ) -> None:
        result = self.analyze("struct Outer { func run() { let value = } }")

        self.assertEqual(result.decision.value, "partial")
        self.assertTrue(result.diagnostics)

    def test_type_keyword_is_not_recorded_as_a_method_modifier(self) -> None:
        result = self.analyze("public class C { class func make() {} }")

        self.assertEqual(result.declarations[0].modifiers, ["public"])
        self.assertEqual(result.declarations[1].modifiers, ["class"])

    def test_file_confined_helpers_preserve_visibility_without_losing_declarations(
        self,
    ) -> None:
        result = self.analyze("""class Loader {}
private class PrivateHelper {}
fileprivate struct FileHelper {}
internal class SharedHelper {}
public struct PublicHelper {}
struct DefaultHelper {}
""")

        self.assertEqual(
            [entry.unit.name for entry in result.declarations],
            [
                "Loader",
                "PrivateHelper",
                "FileHelper",
                "SharedHelper",
                "PublicHelper",
                "DefaultHelper",
            ],
        )
        self.assertEqual(
            [entry.modifiers for entry in result.declarations],
            [[], ["private"], ["fileprivate"], ["internal"], ["public"], []],
        )
        self.assertTrue(all(not entry.scopes for entry in result.declarations))
        self.assertEqual([entry.unit for entry in result.declarations], result.units)

    def test_inventory_distinguishes_extension_conformance_from_consumed_contract(
        self,
    ) -> None:
        result = self.analyze("""protocol UserLoading { func load() }
protocol UserCacheReading { func read() }
class UserLoader { let cache: any UserCacheReading }
extension UserLoader: UserLoading { func load() {} }
""")

        top_level = [entry for entry in result.declarations if not entry.scopes]
        self.assertEqual(
            [entry.unit.kind.value for entry in top_level],
            ["protocol", "protocol", "class", "extension"],
        )
        self.assertEqual(top_level[2].unit.signature.inherited_types, [])
        self.assertEqual(top_level[3].unit.signature.name.tokens, ["UserLoader"])
        self.assertEqual(
            [base.tokens for base in top_level[3].unit.signature.inherited_types],
            [["UserLoading"]],
        )
        self.assertEqual(top_level[2].unit.members[0].name, "cache")
        implementation = result.declarations[-1]
        self.assertEqual(implementation.unit.name, "load")
        self.assertEqual(implementation.scopes[0].name, "UserLoader")
