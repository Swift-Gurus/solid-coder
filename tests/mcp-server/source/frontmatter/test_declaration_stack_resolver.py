"""
solid-name: TestDeclarationStackResolver
solid-category: unit-test
solid-spec: [SPEC-069]
solid-description: Verifies metadata stack evidence belongs to each declaration rather than its neighboring imports or text.
"""

import unittest

from source.frontmatter.declaration_stack_resolver import DeclarationStackResolver
from source.frontmatter.stack_registration import StackRegistration
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.swift_source_analyzer_factory import SwiftSourceAnalyzerFactory


class TestDeclarationStackResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = DeclarationStackResolver([
            StackRegistration(tag="swiftui", file_extensions=[".swift"], modules=["SwiftUI"], signals=["View", "Text"]),
            StackRegistration(tag="structured-concurrency", file_extensions=[".swift"], signals=["async", "await", "Task"]),
        ])

    def test_only_the_view_has_framework_evidence(self) -> None:
        analysis = self._analyze('import SwiftUI\nstruct User { let name: String }\nstruct ProfileView: View { var body: some View { Text("Hi") } }')
        detections = self.resolver.parse(analysis)
        self.assertEqual([entry.scope_identity for entry in detections], [analysis.declarations[1].unit.identity])
        self.assertEqual([entry.tag for entry in detections], ["swiftui"])
        self.assertEqual(detections[0].evidence[0].span.start, 3)

    def test_imports_comments_and_literals_alone_do_not_impose_stack(self) -> None:
        analysis = self._analyze('import SwiftUI\n// Task await View\nstruct User { let name = "View Task" }')
        self.assertEqual(self.resolver.parse(analysis), [])

    def test_concurrency_uses_declaration_syntax_without_module_import(self) -> None:
        analysis = self._analyze("struct Loader { func load() async {} }")
        detections = self.resolver.parse(analysis)
        self.assertTrue(detections)
        self.assertTrue(all(entry.tag == "structured-concurrency" for entry in detections))
        self.assertIn(analysis.declarations[0].unit.identity, [entry.scope_identity for entry in detections])

    def test_unimported_framework_names_do_not_imply_framework_ownership(self) -> None:
        self.assertEqual(self.resolver.parse(self._analyze("protocol View {}")), [])

    def _analyze(self, text: str):
        return SwiftSourceAnalyzerFactory().make().analyze(ResolvedAnalysisSource(
            identity="/unwritten/Target.swift", file_extension=".swift", text=text,
        ))
