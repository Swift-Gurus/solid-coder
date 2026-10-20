import unittest

from source.analyze_source_input import AnalyzeSourceInput
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.text_analysis_source import TextAnalysisSource
from source.analysis.declarations.source_declaration_selection import SourceDeclarationSelection
from source.analysis.declarations.select_source_declarations_input import SelectSourceDeclarationsInput
from source.analysis.declarations.select_source_declarations_operation import SelectSourceDeclarationsOperation
from source.analysis.declarations.source_declaration_inventory_renderer import SourceDeclarationInventoryRenderer


"""
solid-name: TestSourceDeclarationSelection
solid-category: integration-test
solid-spec: [SPEC-066]
solid-description: Verifies authored structural selection preserves source order, exact identities, compact metadata and analysis limitations without rule-specific parsing.
"""
class TestSourceDeclarationSelection(unittest.TestCase):
    def setUp(self) -> None:
        self.operation = SelectSourceDeclarationsOperation(SourceDeclarationInventoryRenderer())

    def test_selects_file_types_static_functions_and_local_types_without_duplicates(self) -> None:
        analysis = SourceAnalysisOperationFactory().make().execute(AnalyzeSourceInput(
            source=TextAnalysisSource(virtual_path="Example.swift", text="""protocol Loading {}
class Loader: Loading {
    static func make() { struct Local {} }
    func load() {}
    struct Nested {}
}
func global() {}
"""),
        ))
        result = self.operation.execute(SelectSourceDeclarationsInput(
            analysis=analysis,
            selections=[
                SourceDeclarationSelection(kinds=["class", "struct", "protocol"], scopes=["file"]),
                SourceDeclarationSelection(kinds=["function"], scopes=["file"]),
                SourceDeclarationSelection(kinds=["function"], any_modifiers=["static", "class"]),
                SourceDeclarationSelection(kinds=["struct", "enum"], scopes=["callable"]),
                SourceDeclarationSelection(kinds=["class"], scopes=["file"]),
            ],
        ))

        self.assertEqual([entry.unit.name for entry in result.declarations],
                         ["Loading", "Loader", "make", "Local", "global"])
        self.assertEqual(len(set(entry.identity for entry in result.declarations)), 5)
        self.assertEqual(result.limitations, [])
        self.assertIn("Loader", result.context)
        self.assertIn("declaration:", result.context)
        self.assertNotIn("static func make()", result.context)
        self.assertNotIn("struct Nested", result.context)

    def test_unsupported_analysis_is_unavailable_not_an_empty_complete_inventory(self) -> None:
        analysis = SourceAnalysisOperationFactory().make().execute(AnalyzeSourceInput(
            source=TextAnalysisSource(virtual_path="Example.py", text="class Loader: pass"),
        ))

        result = self.operation.execute(SelectSourceDeclarationsInput(
            analysis=analysis, selections=[SourceDeclarationSelection(kinds=["class"])],
        ))

        self.assertEqual(result.declarations, [])
        self.assertTrue(result.limitations)
