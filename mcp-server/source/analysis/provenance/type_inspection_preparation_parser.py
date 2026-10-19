"""Selects authoritative source inspections before semantic lookup."""

from findings.review_unit_kind import ReviewUnitKind
from harness.flow_validation_error import FlowValidationError
from source.analysis.provenance.prepared_type_inspections import PreparedTypeInspections
from source.analysis.provenance.resolve_type_inspections_input import ResolveTypeInspectionsInput
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.resolved_source_analyzing import ResolvedSourceAnalyzing
from source.source_analysis_decision import SourceAnalysisDecision
from source.source_language_detecting import SourceLanguageDetecting


"""
solid-name: TypeInspectionPreparationParser
solid-category: service
solid-spec: [SPEC-064]
solid-description: Selects a target's exact inspection inventory from its authoritative source snapshot.
"""
class TypeInspectionPreparationParser(SourceSyntaxParsing[ResolveTypeInspectionsInput, PreparedTypeInspections]):
    def __init__(self, analyzer: ResolvedSourceAnalyzing, languages: SourceLanguageDetecting) -> None:
        self._analyzer = analyzer
        self._languages = languages

    def parse(self, source: ResolveTypeInspectionsInput) -> PreparedTypeInspections:
        snapshots = [snapshot for snapshot in source.context.sources if snapshot.source_identity == source.target.source_identity]
        if len(snapshots) != 1:
            raise FlowValidationError("Type inspection requires exactly one authoritative source snapshot for the selected target.")
        snapshot = snapshots[0]
        resolved = ResolvedAnalysisSource(identity=snapshot.source_identity, file_extension=source.file_extension, text=snapshot.content)
        analysis = self._analyzer.analyze(resolved)
        if source.target.kind is ReviewUnitKind.DOCUMENT:
            code = snapshot.content
            inspections = analysis.type_inspections
        else:
            units = [unit for unit in analysis.units if unit.identity == source.target.unit_identity]
            if len(units) != 1:
                raise FlowValidationError("The selected inspection target does not identify one declaration in its source snapshot.")
            unit = units[0]
            code = snapshot.content.encode("utf-8")[unit.start_offset:unit.end_offset + 1].decode("utf-8")
            inspections = [inspection for inspection in analysis.type_inspections if unit.start_offset <= inspection.start_offset and inspection.end_offset <= unit.end_offset + 1]
        if code != source.target.code:
            raise FlowValidationError("The inspection target code does not match its authoritative source snapshot.")
        limitations = []
        if analysis.decision is not SourceAnalysisDecision.PARSED:
            limitations.append(f"Source inventory is {analysis.decision.value}; inspection coverage is not complete.")
        limitations.extend(f"{diagnostic.code} at line {diagnostic.line}: {diagnostic.message}" for diagnostic in analysis.diagnostics)
        return PreparedTypeInspections(
            snapshot=snapshot, language=self._languages.detect(resolved),
            inspections=inspections, limitations=limitations,
        )
