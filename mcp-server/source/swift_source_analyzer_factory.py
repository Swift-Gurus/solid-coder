"""Composes deterministic Swift source analysis."""

import tempfile

from common.callable_temporary_directory_provider import (
    CallableTemporaryDirectoryProvider,
)
from findings.review_unit_kind_parser import ReviewUnitKindParser
from findings.utf8_text_file_writer import Utf8TextFileWriter
from harness.json_loading import JsonLoader
from harness.process_execution_runner_adapter import ProcessExecutionRunnerAdapter
from hook_utils import SubprocessAdapter
from source.source_evidence_resolver import SourceEvidenceResolver
from source.swift_ast_item_decoder import SwiftASTItemDecoder
from source.swift_ast_items_loader import SwiftASTItemsLoader
from source.swift_ast_unit_decoder import SwiftASTUnitDecoder
from source.swift_ast_unit_kind_resolver import SwiftASTUnitKindResolver
from source.swift_ast_unit_name_resolver import SwiftASTUnitNameResolver
from source.swift_import_tag_detector import SwiftImportTagDetector
from source.swift_import_tag_registration import SwiftImportTagRegistration
from source.swift_parse_diagnostics_resolver import SwiftParseDiagnosticsResolver
from source.swift_parser_runner import SwiftParserRunner
from source.swift_source_analyzer import SwiftSourceAnalyzer
from source.swift_tag_detector import SwiftTagDetector
from source.swift_view_declaration_qualifier import SwiftViewDeclarationQualifier
from source.swift_view_tag_detector import SwiftViewTagDetector
from source.utf8_source_offset_line_resolver import UTF8SourceOffsetLineResolver


"""
solid-name: SwiftSourceAnalyzerFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Provides parsed Swift units, diagnostics, and auditable built-in technology detections from immutable source.
"""
class SwiftSourceAnalyzerFactory:
    def make(self) -> SwiftSourceAnalyzer:
        json_loader = JsonLoader()
        items_loader = SwiftASTItemsLoader(json_loader)
        name_resolver = SwiftASTUnitNameResolver()
        line_resolver = UTF8SourceOffsetLineResolver()
        evidence_resolver = SourceEvidenceResolver(line_resolver)
        return SwiftSourceAnalyzer(
            parser=SwiftParserRunner(
                directories=CallableTemporaryDirectoryProvider(
                    tempfile.TemporaryDirectory
                ),
                writer=Utf8TextFileWriter(),
                process_runner=ProcessExecutionRunnerAdapter(
                    SubprocessAdapter()
                ),
            ),
            units=SwiftASTUnitDecoder(
                items_loader=items_loader,
                item_decoder=SwiftASTItemDecoder(
                    kind_resolver=SwiftASTUnitKindResolver(
                        ReviewUnitKindParser()
                    ),
                    name_resolver=name_resolver,
                    line_resolver=line_resolver,
                ),
            ),
            diagnostics=SwiftParseDiagnosticsResolver(),
            tag_detector=SwiftTagDetector([
                SwiftImportTagDetector(
                    json_loader=json_loader,
                    evidence_resolver=evidence_resolver,
                    registrations=[
                        SwiftImportTagRegistration(
                            module="SwiftUI",
                            tags=["ui", "swiftui"],
                        ),
                        SwiftImportTagRegistration(
                            module="UIKit",
                            tags=["ui", "uikit"],
                        ),
                        SwiftImportTagRegistration(
                            module="ComposableArchitecture",
                            tags=["tca"],
                        ),
                        SwiftImportTagRegistration(
                            module="Dispatch",
                            tags=["concurrency", "gcd"],
                        ),
                    ],
                ),
                SwiftViewTagDetector(
                    items_loader=items_loader,
                    declaration_qualifier=SwiftViewDeclarationQualifier(
                        name_resolver
                    ),
                    evidence_resolver=evidence_resolver,
                ),
            ]),
        )
