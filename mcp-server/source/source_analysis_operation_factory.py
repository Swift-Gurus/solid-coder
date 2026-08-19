"""Composes deterministic source-analysis operation dependencies."""

import tempfile
from pathlib import Path

from common.callable_temporary_directory_provider import (
    CallableTemporaryDirectoryProvider,
)
from findings.review_unit_kind_parser import ReviewUnitKindParser
from findings.utf8_text_file_writer import Utf8TextFileWriter
from gate.dict_extension_lookup import DictExtensionLookup
from harness.json_loading import JsonLoader
from harness.path_builder import PathBuilder
from harness.path_canonicalizer import PathCanonicalizer
from harness.process_execution_runner_adapter import ProcessExecutionRunnerAdapter
from hook_utils import SubprocessAdapter
from hooks.pathlib_extractor import PathlibExtractor
from source.analysis_source_dispatch_visitor import AnalysisSourceDispatchVisitor
from source.analysis_source_resolver import AnalysisSourceResolver
from source.file_analysis_source_resolver import FileAnalysisSourceResolver
from source.language_source_analyzer_registration import (
    LanguageSourceAnalyzerRegistration,
)
from source.language_source_analyzer_resolver import (
    LanguageSourceAnalyzerResolver,
)
from source.source_analysis_operation import SourceAnalysisOperation
from source.source_language_detector import SourceLanguageDetector
from source.swift_ast_unit_decoder import SwiftASTUnitDecoder
from source.swift_ast_item_decoder import SwiftASTItemDecoder
from source.swift_ast_items_loader import SwiftASTItemsLoader
from source.swift_ast_unit_kind_resolver import SwiftASTUnitKindResolver
from source.swift_ast_unit_name_resolver import SwiftASTUnitNameResolver
from source.swift_parse_diagnostics_resolver import SwiftParseDiagnosticsResolver
from source.swift_parser_runner import SwiftParserRunner
from source.swift_source_analyzer import SwiftSourceAnalyzer
from source.text_analysis_source_resolver import TextAnalysisSourceResolver
from source.utf8_source_offset_line_resolver import UTF8SourceOffsetLineResolver
from utils.prompt_builder import PlainTextFileReader


"""
solid-name: SourceAnalysisOperationFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Composes deterministic file and text source-analysis capabilities.
"""
class SourceAnalysisOperationFactory:
    def make(self) -> SourceAnalysisOperation:
        process_runner = ProcessExecutionRunnerAdapter(SubprocessAdapter())
        swift_analyzer = SwiftSourceAnalyzer(
            parser=SwiftParserRunner(
                directories=CallableTemporaryDirectoryProvider(
                    tempfile.TemporaryDirectory
                ),
                writer=Utf8TextFileWriter(),
                process_runner=process_runner,
            ),
            units=SwiftASTUnitDecoder(
                items_loader=SwiftASTItemsLoader(JsonLoader()),
                item_decoder=SwiftASTItemDecoder(
                    kind_resolver=SwiftASTUnitKindResolver(
                        ReviewUnitKindParser()
                    ),
                    name_resolver=SwiftASTUnitNameResolver(),
                    line_resolver=UTF8SourceOffsetLineResolver(),
                ),
            ),
            diagnostics=SwiftParseDiagnosticsResolver(),
        )
        return SourceAnalysisOperation(
            source_resolver=AnalysisSourceResolver(
                AnalysisSourceDispatchVisitor(
                    file_resolver=FileAnalysisSourceResolver(
                        PlainTextFileReader()
                    ),
                    text_resolver=TextAnalysisSourceResolver(
                        PathCanonicalizer(PathBuilder())
                    ),
                )
            ),
            language_detector=SourceLanguageDetector(
                extension_extractor=PathlibExtractor(
                    lambda path: Path(path).suffix.lower()
                ),
                extension_lookup=DictExtensionLookup({
                    ".swift": "swift",
                    ".py": "python",
                }),
            ),
            analyzer_resolver=LanguageSourceAnalyzerResolver([
                LanguageSourceAnalyzerRegistration(
                    language="swift",
                    analyzer=swift_analyzer,
                )
            ]),
        )
