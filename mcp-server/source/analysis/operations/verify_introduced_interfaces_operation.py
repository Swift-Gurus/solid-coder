from findings.review_unit_kind import ReviewUnitKind
from harness.content_hashing import ContentHashing
from harness.operation_handling import OperationHandling
from harness.path_building import PathBuilding
from source.analysis.operations.source_introduction_evidence import SourceIntroductionEvidence
from source.analyze_source_input import AnalyzeSourceInput
from source.source_analysis import SourceAnalysis
from source.source_analysis_decision import SourceAnalysisDecision
from source.source_bytes_reading import SourceBytesReading
from source.source_unit_identity import SourceUnitIdentity
from source.text_analysis_source import TextAnalysisSource


"""
solid-name: VerifyIntroducedInterfacesOperation
solid-category: service
solid-spec: [SPEC-057]
solid-description: Verifies newly introduced source interfaces with explicit uncertainty and auditable evidence.
"""
class VerifyIntroducedInterfacesOperation(OperationHandling[TextAnalysisSource, SourceIntroductionEvidence]):
    def __init__(
        self,
        reader: SourceBytesReading,
        analyzer: OperationHandling[AnalyzeSourceInput, SourceAnalysis],
        paths: PathBuilding,
        hasher: ContentHashing,
    ) -> None:
        self._reader = reader
        self._analyzer = analyzer
        self._paths = paths
        self._hasher = hasher

    def execute(self, operation_input: TextAnalysisSource) -> SourceIntroductionEvidence:
        if operation_input.virtual_path is None:
            return SourceIntroductionEvidence(
                reasoning="The original source cannot be identified.",
                evidence="No source path was supplied.",
            )
        try:
            original = self._reader.read(self._paths.build(operation_input.virtual_path)).decode("utf-8")
        except FileNotFoundError:
            original = ""
        except (OSError, UnicodeError) as error:
            return SourceIntroductionEvidence(
                reasoning="The original source could not be read.", evidence=str(error),
            )

        before = self._analyzer.execute(AnalyzeSourceInput(source=TextAnalysisSource(
            text=original,
            virtual_path=operation_input.virtual_path,
            file_extension=operation_input.file_extension,
        )))
        after = self._analyzer.execute(AnalyzeSourceInput(source=operation_input))
        evidence = (
            f"Source {after.source_identity}; original sha256 {self._hasher.hash(original.encode('utf-8'))}; "
            f"proposed sha256 {self._hasher.hash(operation_input.text.encode('utf-8'))}."
        )
        if any(analysis.decision is not SourceAnalysisDecision.PARSED or analysis.diagnostics for analysis in [before, after]):
            return SourceIntroductionEvidence(
                reasoning="Complete parsing of both source versions is required.", evidence=evidence,
            )
        original_names = {unit.name for unit in before.units}
        proposed_names = [unit.name for unit in after.units]
        return SourceIntroductionEvidence(
            verified_interfaces=[
                SourceUnitIdentity(source_identity=after.source_identity, unit_identity=unit.identity)
                for unit in after.units
                if unit.kind is ReviewUnitKind.PROTOCOL
                and unit.name not in original_names
                and proposed_names.count(unit.name) == 1
            ],
            reasoning="Only unambiguous interfaces absent from the original source and present in the parsed proposed source are verified new.",
            evidence=evidence,
        )
