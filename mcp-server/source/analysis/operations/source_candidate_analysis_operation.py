from harness.operation_handling import OperationHandling
from source.analysis.operations.candidate_source_analysis_visitor import (
    CandidateSourceVisitor,
)
from source.analysis.operations.source_candidate_analyses import SourceCandidateAnalyses
from source.analyze_source_input import AnalyzeSourceInput
from source.read_source_candidates_input import ReadSourceCandidatesInput
from source.read_source_candidates_output import ReadSourceCandidatesOutput
from source.source_analysis import SourceAnalysis
from source.text_analysis_source import TextAnalysisSource

"""
solid-name: SourceCandidateAnalysisOperation
solid-category: service
solid-spec: [SPEC-057]
solid-description: Analyzes verified repository candidates and authoritative prospective snapshots once per source while retaining unreadable, truncated, and partial-analysis evidence.
"""


class SourceCandidateAnalysisOperation(
    OperationHandling[ReadSourceCandidatesInput, SourceCandidateAnalyses]
):
    def __init__(
        self,
        reader: OperationHandling[
            ReadSourceCandidatesInput, ReadSourceCandidatesOutput
        ],
        analyzer: OperationHandling[AnalyzeSourceInput, SourceAnalysis],
        candidate_visitor: CandidateSourceVisitor[SourceCandidateAnalyses],
    ) -> None:
        self._reader = reader
        self._analyzer = analyzer
        self._candidate_visitor = candidate_visitor

    def execute(
        self, operation_input: ReadSourceCandidatesInput
    ) -> SourceCandidateAnalyses:
        sources = [
            TextAnalysisSource(text=snapshot.content, virtual_path=str(snapshot.path))
            for snapshot in operation_input.context.sources
        ]
        known_paths = {source.virtual_path for source in sources}
        limitations: list[str] = []
        candidates = ReadSourceCandidatesInput(
            candidates=[
                candidate
                for candidate in operation_input.candidates
                if str(candidate.path) not in known_paths
            ],
            context=operation_input.context,
            max_bytes_per_candidate=operation_input.max_bytes_per_candidate,
        )
        analyses = [
            self._analyzer.execute(AnalyzeSourceInput(source=source))
            for source in sources
        ]
        for result in self._reader.execute(candidates).results:
            if str(result.candidate.path) not in known_paths:
                inspected = result.accept(self._candidate_visitor)
                analyses.extend(inspected.analyses)
                sources.extend(inspected.sources)
                limitations.extend(inspected.limitations)
                known_paths.add(str(result.candidate.path))
        limitations.extend(
            f"{analysis.source_identity}:{diagnostic.line}: {diagnostic.message}"
            for analysis in analyses
            for diagnostic in analysis.diagnostics
        )
        return SourceCandidateAnalyses(
            analyses=analyses, sources=sources, limitations=limitations
        )
