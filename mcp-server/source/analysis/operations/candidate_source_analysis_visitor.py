from typing import Protocol, TypeVar

from harness.operation_handling import OperationHandling
from source.analysis.operations.source_candidate_analyses import SourceCandidateAnalyses
from source.analyze_source_input import AnalyzeSourceInput
from source.loaded_candidate_source import LoadedCandidateSource
from source.source_analysis import SourceAnalysis
from source.text_analysis_source import TextAnalysisSource
from source.unavailable_candidate_source import UnavailableCandidateSource

VisitResult_co = TypeVar("VisitResult_co", covariant=True)


"""
solid-name: CandidateSourceVisitor
solid-category: abstraction
solid-spec: [SPEC-057]
solid-description: Contract for handling verified and unavailable candidate-read outcomes polymorphically.
"""


class CandidateSourceVisitor(Protocol[VisitResult_co]):
    def visit_loaded(self, source: LoadedCandidateSource) -> VisitResult_co: ...

    def visit_unavailable(
        self, source: UnavailableCandidateSource
    ) -> VisitResult_co: ...


"""
solid-name: CandidateSourceAnalysisVisitor
solid-category: service
solid-spec: [SPEC-057]
solid-description: Converts candidate-read outcomes into bounded source analyses or explicit inspection limitations.
"""


class CandidateSourceAnalysisVisitor(CandidateSourceVisitor[SourceCandidateAnalyses]):
    def __init__(
        self, analyzer: OperationHandling[AnalyzeSourceInput, SourceAnalysis]
    ) -> None:
        self._analyzer = analyzer

    def visit_loaded(self, source: LoadedCandidateSource) -> SourceCandidateAnalyses:
        if source.truncated:
            return SourceCandidateAnalyses(
                limitations=[
                    f"{source.candidate.path}: source exceeds the inspection limit",
                ]
            )
        snapshot = TextAnalysisSource(
            text=source.content, virtual_path=str(source.candidate.path)
        )
        return SourceCandidateAnalyses(
            analyses=[self._analyzer.execute(AnalyzeSourceInput(source=snapshot))],
            sources=[snapshot],
        )

    def visit_unavailable(
        self, source: UnavailableCandidateSource
    ) -> SourceCandidateAnalyses:
        return SourceCandidateAnalyses(
            limitations=[f"{source.candidate.path}: {source.detail}"]
        )
