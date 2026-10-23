"""Coordinates language-selected provenance for a prepared inspection inventory."""

from harness.flow_validation_error import FlowValidationError
from harness.operation_handling import OperationHandling
from harness.project_context import ProjectDirectoryReading
from harness.template_value_rendering import TemplateValueRendering
from source.analysis.provenance.prepared_type_inspections import PreparedTypeInspections
from source.analysis.provenance.resolve_type_inspections_input import (
    ResolveTypeInspectionsInput,
)
from source.analysis.provenance.resolved_type_inspections import ResolvedTypeInspections
from source.analysis.provenance.source_symbol_ownership import SourceSymbolOwnership
from source.analysis.provenance.source_symbol_provenance import SourceSymbolProvenance
from source.analysis.provenance.source_type_inspection_provenance import (
    SourceTypeInspectionProvenance,
)
from source.analysis.provenance.source_unresolved_symbol import SourceUnresolvedSymbol
from source.analysis.provenance.sourcekit_document_factory import (
    SemanticDocumentOpening,
)
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.analysis.type_inspections.source_type_inspection import SourceTypeInspection
from source.language_source_analyzer_resolving import LanguageSourceAnalyzerResolving

"""
solid-name: SourceTypeInspectionOperation
solid-category: service
solid-spec: [SPEC-064]
solid-description: Resolves ordered inspection provenance while preserving incomplete evidence and successful earlier resolutions.
"""


class SourceTypeInspectionOperation(
    OperationHandling[ResolveTypeInspectionsInput, ResolvedTypeInspections]
):
    def __init__(
        self,
        preparation: SourceSyntaxParsing[
            ResolveTypeInspectionsInput, PreparedTypeInspections
        ],
        sessions: LanguageSourceAnalyzerResolving[
            SemanticDocumentOpening[
                SourceSyntaxParsing[
                    SourceTypeInspection, SourceTypeInspectionProvenance
                ]
            ]
        ],
        project_directory: ProjectDirectoryReading,
        renderer: TemplateValueRendering[list[SourceTypeInspectionProvenance]],
    ) -> None:
        self._preparation = preparation
        self._sessions = sessions
        self._project_directory = project_directory
        self._renderer = renderer

    def execute(
        self, operation_input: ResolveTypeInspectionsInput
    ) -> ResolvedTypeInspections:
        prepared = self._preparation.parse(operation_input)
        if not prepared.inspections:
            return ResolvedTypeInspections(limitations=prepared.limitations)
        project_root = self._project_directory.read().resolve()
        sessions = self._sessions.resolve(prepared.language)
        unopened_sources = {
            snapshot.path.resolve()
            for snapshot in operation_input.context.sources
            if snapshot.source_identity != prepared.snapshot.source_identity
        }
        results: list[SourceTypeInspectionProvenance] = []
        limitations = list(prepared.limitations)
        failure: str | None = None
        if sessions is None:
            failure = f"No semantic inspection capability is registered for language '{prepared.language}'."
        else:
            try:
                with sessions.open(prepared.snapshot, project_root) as parser:
                    for inspection in prepared.inspections:
                        resolved = parser.parse(inspection)
                        if resolved.inspection != inspection:
                            raise ValueError(
                                "The semantic provider changed the prepared inspection identity or source facts."
                            )
                        if any(
                            role.declaration_path is not None
                            and role.declaration_path.resolve() in unopened_sources
                            for role in (
                                resolved.value,
                                resolved.contract,
                                resolved.destination,
                            )
                        ):
                            resolved = SourceTypeInspectionProvenance(
                                inspection=resolved.inspection,
                                value=resolved.value,
                                contract=resolved.contract,
                                destination=resolved.destination,
                                verified=False,
                                limitations=[
                                    *resolved.limitations,
                                    "A referenced prospective sibling source was not opened in this semantic session; its on-disk declaration cannot verify the pending buffer.",
                                ],
                            )
                        results.append(resolved)
            except (OSError, ValueError, FlowValidationError) as error:
                failure = f"Semantic inspection resolution is incomplete: {error}"
        if failure is not None:
            limitations.append(failure)
            unknown = SourceSymbolProvenance(
                resolution=SourceUnresolvedSymbol(reason=failure),
                project_root=project_root,
                ownership=SourceSymbolOwnership.UNKNOWN,
                declaration_path=None,
                reason=failure,
            )
            results.extend(
                SourceTypeInspectionProvenance(
                    inspection=inspection,
                    value=unknown,
                    contract=unknown,
                    destination=unknown,
                    verified=False,
                    limitations=[failure],
                )
                for inspection in prepared.inspections[len(results) :]
            )
        limitations.extend(
            reason for result in results for reason in result.limitations
        )
        return ResolvedTypeInspections(
            inspections=results,
            limitations=limitations,
            context=self._renderer.render(results),
        )
