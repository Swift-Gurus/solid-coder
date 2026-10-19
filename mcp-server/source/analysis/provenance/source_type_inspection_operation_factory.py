"""Composes language-selected semantic inspection resolution."""

from gate.default_exclusion_checker_factory import DefaultExclusionCheckerFactory
from harness.project_context import ProjectDirectoryReading
from source.analysis.provenance.source_type_inspection_operation import SourceTypeInspectionOperation
from source.analysis.provenance.sourcekit_document_factory import SourceKitDocumentFactory
from source.analysis.provenance.swift_inspection_session_factory import SwiftInspectionSessionFactory
from source.analysis.provenance.type_inspection_preparation_parser import TypeInspectionPreparationParser
from source.analysis.provenance.type_inspection_context_renderer import TypeInspectionContextRenderer
from source.language_source_analyzer_registration import LanguageSourceAnalyzerRegistration
from source.language_source_analyzer_resolver import LanguageSourceAnalyzerResolver
from source.resolved_source_analyzer_factory import ResolvedSourceAnalyzerFactory
from source.source_language_detector_factory import SourceLanguageDetectorFactory


"""
solid-name: SourceTypeInspectionOperationFactory
solid-category: factory
solid-spec: [SPEC-064]
solid-description: Composes prepared source inspection and language-specific semantic session capabilities.
"""
class SourceTypeInspectionOperationFactory:
    def __init__(self, project_directory: ProjectDirectoryReading) -> None:
        self._project_directory = project_directory

    def make(self) -> SourceTypeInspectionOperation:
        return SourceTypeInspectionOperation(
            preparation=TypeInspectionPreparationParser(
                analyzer=ResolvedSourceAnalyzerFactory().make(),
                languages=SourceLanguageDetectorFactory().make(),
            ),
            sessions=LanguageSourceAnalyzerResolver([
                LanguageSourceAnalyzerRegistration(
                    language="swift",
                    analyzer=SwiftInspectionSessionFactory(
                        documents=SourceKitDocumentFactory(),
                        exclusions=DefaultExclusionCheckerFactory(),
                    ),
                ),
            ]),
            project_directory=self._project_directory,
            renderer=TypeInspectionContextRenderer(),
        )
