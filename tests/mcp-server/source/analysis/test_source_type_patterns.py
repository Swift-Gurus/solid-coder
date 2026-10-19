"""Pattern type inspections through the production source-analysis boundary."""

import unittest

from source.analyze_source_input import AnalyzeSourceInput
from source.source_analysis_decision import SourceAnalysisDecision
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.text_analysis_source import TextAnalysisSource


"""
solid-name: TestSourceTypePatterns
solid-category: integration-test
solid-spec: [SPEC-063]
solid-description: Verifies Swift pattern inspection coverage, exact evidence and honest implicit operands through source analysis.
"""
class TestSourceTypePatterns(unittest.TestCase):
    def setUp(self) -> None:
        self.operation = SourceAnalysisOperationFactory().make()

    def test_switch_alternatives_and_nested_patterns_keep_distinct_ranges(self) -> None:
        source = (
            "// 😀\nswitch value {\n"
            "case is Model, is Other: break\n"
            "case (let x as Module.Model, is Other): break\n"
            "case .some(let x as Model): break\n"
            "default: break\n}\n"
        )
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Patterns.swift", text=source,
        )))

        self.assertEqual(result.decision, SourceAnalysisDecision.PARSED)
        facts = result.type_inspections
        self.assertEqual([fact.expression for fact in facts], [
            "is Model", "is Other", "as Module.Model", "is Other", "as Model",
        ])
        self.assertEqual([fact.kind.value for fact in facts], [
            "pattern_type_test", "pattern_type_test", "pattern_cast",
            "pattern_type_test", "pattern_cast",
        ])
        self.assertEqual([fact.operand for fact in facts], [None] * 5)
        self.assertEqual(facts[2].target_tokens, ["Module", ".", "Model"])
        self.assertEqual([fact.span.start for fact in facts], [3, 3, 4, 4, 5])
        self.assertEqual(len({fact.identity for fact in facts}), 5)
        self.assertEqual([fact.start_offset for fact in facts], sorted(fact.start_offset for fact in facts))
        for fact in facts:
            self.assertEqual(
                source.encode("utf-8")[fact.start_offset:fact.end_offset].decode("utf-8"),
                fact.expression,
            )

    def test_conditional_and_iteration_patterns_include_each_clause(self) -> None:
        sources = [
            "if case let x as Model = first, case is Other = second { }",
            "guard case is Model = value else { return }",
            "while case let x as Model = next() { }",
            "if case (let x as Model, is Other) = pair { }",
            "for case let x as Model in values { }",
        ]
        expected = [
            ["as Model", "is Other"], ["is Model"], ["as Model"],
            ["as Model", "is Other"], ["as Model"],
        ]
        for source, expressions in zip(sources, expected):
            with self.subTest(source=source):
                result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
                    virtual_path="Conditional.swift", text=source,
                )))
                self.assertEqual(result.decision, SourceAnalysisDecision.PARSED)
                self.assertEqual([fact.expression for fact in result.type_inspections], expressions)
                self.assertTrue(all(fact.operand is None for fact in result.type_inspections))

    def test_catch_patterns_do_not_fabricate_error_operands(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Catch.swift",
            text="do { try work() } catch is Failure { } catch let e as Other { }",
        )))

        self.assertEqual(result.decision, SourceAnalysisDecision.PARSED)
        self.assertEqual([fact.expression for fact in result.type_inspections], ["is Failure", "as Other"])
        self.assertEqual([fact.operand for fact in result.type_inspections], [None, None])

    def test_guards_and_bodies_keep_expression_kinds_without_duplicates(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Guarded.swift",
            text=(
                "switch value { case let x as Model where x is Other:\n"
                " let y = x as? Third; default: break }"
            ),
        )))

        self.assertEqual([fact.kind.value for fact in result.type_inspections], [
            "pattern_cast", "type_test", "conditional_cast",
        ])
        self.assertEqual([fact.operand for fact in result.type_inspections], [None, "x", "x"])

    def test_comments_between_operator_and_type_are_preserved_as_evidence(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Comments.swift",
            text=(
                '// case is Fake\nlet text = "case let x as Fake"\n'
                "switch value { case is /* comment */\n Module.Model: break; default: break }"
            ),
        )))

        self.assertEqual(len(result.type_inspections), 1)
        fact = result.type_inspections[0]
        self.assertEqual(fact.expression, "is /* comment */\n Module.Model")
        self.assertEqual(fact.target_tokens, ["Module", ".", "Model"])
        self.assertEqual(fact.span.start, 3)
        self.assertEqual(fact.span.end, 4)

    def test_incomplete_pattern_retains_valid_neighbor_and_partial_status(self) -> None:
        result = self.operation.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            virtual_path="Incomplete.swift",
            text="switch value { case is Model: break; case is: break; default: break }",
        )))

        self.assertEqual(result.decision, SourceAnalysisDecision.PARTIAL)
        self.assertTrue(result.diagnostics)
        self.assertEqual([fact.expression for fact in result.type_inspections], ["is Model"])
