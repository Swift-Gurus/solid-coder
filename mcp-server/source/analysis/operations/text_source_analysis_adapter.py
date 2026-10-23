from harness.operation_handling import OperationHandling
from source.analyze_source_input import AnalyzeSourceInput
from source.source_analysis import SourceAnalysis
from source.text_analysis_source import TextAnalysisSource

"""
solid-name: TextSourceAnalysisAdapter
solid-category: adapter
solid-spec: [SPEC-066]
solid-description: Adapts flat text-and-path workflow bindings to the shared source analyzer without reading a potentially stale file from disk.
"""


class TextSourceAnalysisAdapter(OperationHandling[TextAnalysisSource, SourceAnalysis]):
    def __init__(
        self, analyzer: OperationHandling[AnalyzeSourceInput, SourceAnalysis]
    ) -> None:
        self._analyzer = analyzer

    def execute(self, operation_input: TextAnalysisSource) -> SourceAnalysis:
        return self._analyzer.execute(AnalyzeSourceInput(source=operation_input))
