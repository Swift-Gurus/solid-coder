from harness.operation_handling import OperationHandling
from harness.template_value_rendering import TemplateValueRendering
from source.analysis.declarations.select_source_declarations_input import (
    SelectSourceDeclarationsInput,
)
from source.analysis.declarations.source_declaration_selection_result import (
    SourceDeclarationSelectionResult,
)
from source.analysis.declarations.source_scoped_declaration import (
    SourceScopedDeclaration,
)
from source.source_analysis_decision import SourceAnalysisDecision

"""
solid-name: SelectSourceDeclarationsOperation
solid-category: service
solid-spec: [SPEC-066]
solid-description: Selects ordered source declarations using authored structural criteria and preserves analysis limitations before classification.
"""


class SelectSourceDeclarationsOperation(
    OperationHandling[SelectSourceDeclarationsInput, SourceDeclarationSelectionResult]
):
    def __init__(
        self, renderer: TemplateValueRendering[list[SourceScopedDeclaration]]
    ) -> None:
        self._renderer = renderer

    def execute(
        self, operation_input: SelectSourceDeclarationsInput
    ) -> SourceDeclarationSelectionResult:
        analysis = operation_input.analysis
        declarations = [
            entry
            for entry in analysis.declarations
            if any(
                entry.unit.kind in selection.kinds
                and (not selection.scopes or entry.scope_kind in selection.scopes)
                and (
                    not selection.any_modifiers
                    or any(
                        modifier in entry.modifiers
                        for modifier in selection.any_modifiers
                    )
                )
                for selection in operation_input.selections
            )
        ]
        limitations = []
        if analysis.decision is not SourceAnalysisDecision.PARSED:
            limitations.append(
                f"Source analysis of {analysis.source_identity} is {analysis.decision.value}."
            )
            limitations.extend(
                f"Line {diagnostic.line}: {diagnostic.message}"
                for diagnostic in analysis.diagnostics
            )
        return SourceDeclarationSelectionResult(
            declarations=declarations,
            context=self._renderer.render(declarations),
            limitations=limitations,
        )
