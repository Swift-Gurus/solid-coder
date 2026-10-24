"""Type-inspection facts through the real source-analysis boundary."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from git_working_tree_fixture import GitWorkingTreeFixture
from harness.project_context import ProjectDirectory
from source.analysis.tree_sitter_syntax_parser import TreeSitterSyntaxParser
from source.analyze_source_input import AnalyzeSourceInput
from source.file_analysis_source import FileAnalysisSource
from source.source_analysis_decision import SourceAnalysisDecision
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.text_analysis_source import TextAnalysisSource

"""
solid-name: TestSourceTypeInspections
solid-category: integration-test
solid-spec: [SPEC-063]
solid-description: Verifies typed cast and type-query facts, exact source evidence, and completeness through deterministic source analysis.
"""


class TestSourceTypeInspections(unittest.TestCase):
    def setUp(self) -> None:
        self.operation = SourceAnalysisOperationFactory().make()

    def test_extracts_distinct_inspection_kinds_from_one_parse(self) -> None:
        source = (
            "func inspect(_ value: Any) {\n"
            " let conditional = value as? Module.Model\n"
            " let forced = value as! Model\n"
            " let converted = value as AnyObject\n"
            " let matches = value is Model\n"
            " let runtimeType = type(of: value)\n"
            "}\n"
        )
        with patch.object(
            TreeSitterSyntaxParser,
            "parse",
            autospec=True,
            side_effect=TreeSitterSyntaxParser.parse,
        ) as parse:
            result = self.operation.execute(
                AnalyzeSourceInput(
                    source=TextAnalysisSource(
                        virtual_path="Inspection.swift",
                        text=source,
                    )
                )
            )

        self.assertEqual(parse.call_count, 1)
        self.assertEqual(result.decision, SourceAnalysisDecision.PARSED)
        self.assertEqual(
            [fact.kind.value for fact in result.type_inspections],
            [
                "conditional_cast",
                "forced_cast",
                "conversion",
                "type_test",
                "type_query",
            ],
        )
        self.assertEqual(
            [fact.operand for fact in result.type_inspections], ["value"] * 5
        )
        self.assertEqual(
            [fact.target_tokens for fact in result.type_inspections],
            [["Module", ".", "Model"], ["Model"], ["AnyObject"], ["Model"], []],
        )
        self.assertEqual(
            [fact.span.start for fact in result.type_inspections], [2, 3, 4, 5, 6]
        )

    def test_nested_repeated_expressions_keep_unique_utf8_ranges(self) -> None:
        source = (
            "// 😀\nstruct Inspector {\n"
            " func inspect(_ value: Any) {\n"
            "  let a = (value as! Model) is Other; let b = value as! Model\n"
            "  let closure = { value as? [String: Model] }\n"
            " }\n}\n"
        )
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Inspector.swift",
                    text=source,
                )
            )
        )

        facts = result.type_inspections
        self.assertEqual(len(facts), 4)
        self.assertEqual(len({fact.identity for fact in facts}), 4)
        self.assertEqual(
            [fact.start_offset for fact in facts],
            sorted(fact.start_offset for fact in facts),
        )
        self.assertEqual(facts[-1].target_tokens, ["[", "String", ":", "Model", "]"])
        for fact in facts:
            self.assertEqual(
                source.encode("utf-8")[fact.start_offset : fact.end_offset].decode(
                    "utf-8"
                ),
                fact.expression,
            )

    def test_ignores_literal_trivia_and_member_calls_but_keeps_interpolation(
        self,
    ) -> None:
        source = (
            "// value as! Fake\n/* value is Fake */\n"
            "func show(_ value: Any) {\n"
            ' let plain = "value as? Fake; type(of: value)"\n'
            ' let raw = #"value is Fake"#\n'
            ' let interpolated = "result: \\(value is Model)"\n'
            " let memberCall = helper.type(of: value)\n"
            " let wrongLabel = type(value: value)\n"
            " let extraArgument = type(of: value, extra: value)\n"
            "}\n"
        )
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Show.swift",
                    text=source,
                )
            )
        )

        self.assertEqual(
            [fact.expression for fact in result.type_inspections], ["value is Model"]
        )

    def test_file_and_unwritten_buffer_have_equivalent_stable_facts(self) -> None:
        source = "func inspect(_ value: Any) { let result = value as? Model }"
        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            GitWorkingTreeFixture(root).initialize()
            self.operation = SourceAnalysisOperationFactory().make(
                ProjectDirectory(path=root)
            )
            path = root / "New.swift"
            buffer = self.operation.execute(
                AnalyzeSourceInput(
                    source=TextAnalysisSource(
                        virtual_path=str(path),
                        text=source,
                    )
                )
            )
            self.assertFalse(path.exists())
            path.write_text(source, encoding="utf-8")
            file = self.operation.execute(
                AnalyzeSourceInput(source=FileAnalysisSource(path=path))
            )

        self.assertEqual(buffer.type_inspections, file.type_inspections)
        self.assertEqual(len(buffer.type_inspections), 1)

    def test_partial_source_keeps_complete_occurrences_and_diagnostics(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Partial.swift",
                    text="func inspect(_ value: Any) { let a = value as? Model }\nclass Broken {\n",
                )
            )
        )

        self.assertEqual(result.decision, SourceAnalysisDecision.PARTIAL)
        self.assertTrue(result.diagnostics)
        self.assertEqual(
            [fact.expression for fact in result.type_inspections], ["value as? Model"]
        )

    def test_unsupported_analysis_does_not_claim_complete_empty_inventory(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="inspection.unknown",
                    text="value as? Model",
                )
            )
        )

        self.assertEqual(result.decision, SourceAnalysisDecision.WHOLE_FILE_UNSUPPORTED)
        self.assertEqual(result.type_inspections, [])

    def test_qualified_runtime_query_preserves_its_operand(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Qualified.swift",
                    text="let result = Swift.type(of: container.value)",
                )
            )
        )

        self.assertEqual(len(result.type_inspections), 1)
        self.assertEqual(result.type_inspections[0].kind.value, "type_query")
        self.assertEqual(result.type_inspections[0].operand, "container.value")
        self.assertEqual(result.type_inspections[0].target_tokens, [])

    def test_incomplete_cast_does_not_invent_a_target(self) -> None:
        result = self.operation.execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(
                    virtual_path="Incomplete.swift",
                    text="func inspect(_ value: Any) { let result = value as? }",
                )
            )
        )

        self.assertEqual(result.decision, SourceAnalysisDecision.PARTIAL)
        self.assertTrue(result.diagnostics)
        self.assertEqual(result.type_inspections, [])
