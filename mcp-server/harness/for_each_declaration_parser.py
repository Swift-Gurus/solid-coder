"""Decodes typed workflow iteration declarations."""

from collections.abc import Mapping

from harness.flow_validation_error import FlowValidationError
from harness.for_each_declaration import ForEachDeclaration
from harness.for_each_declaration_parsing import ForEachDeclarationParsing
from harness.for_each_mode import ForEachMode
from harness.for_each_reference_parsing import ForEachReferenceParsing
from harness.workflow_expression_parsing import WorkflowExpressionParsing

_AUTHORED_FIELDS = frozenset({"source", "mode", "label"})
_SNAPSHOT_REFERENCE_FIELDS = frozenset({"step_id", "output_name"})


"""
solid-name: ForEachDeclarationParser
solid-category: boundary
solid-spec: [SPEC-030, SPEC-042]
solid-description: Decodes scalar, authored object, and persisted workflow iteration forms into one typed declaration.
"""
class ForEachDeclarationParser(ForEachDeclarationParsing):
    def __init__(
        self,
        reference_parser: ForEachReferenceParsing,
        expression_parser: WorkflowExpressionParsing,
    ) -> None:
        self._reference_parser = reference_parser
        self._expression_parser = expression_parser

    def parse(
        self,
        step_id: str,
        raw: object,
    ) -> ForEachDeclaration:
        if not isinstance(raw, Mapping):
            return ForEachDeclaration(
                source=self._reference_parser.parse(step_id, raw),
            )

        fields = frozenset(raw)
        if fields.issubset(_SNAPSHOT_REFERENCE_FIELDS):
            return ForEachDeclaration(
                source=self._reference_parser.parse(step_id, raw),
            )
        unknown_fields = sorted(fields - _AUTHORED_FIELDS)
        if unknown_fields:
            raise FlowValidationError(
                f"Step '{step_id}' for_each contains unknown fields: "
                f"{', '.join(unknown_fields)}"
            )

        source = raw.get("source")
        if source is None:
            raise FlowValidationError(
                f"Step '{step_id}' for_each must declare source"
            )
        mode = self._mode(step_id, raw.get("mode", ForEachMode.INDIVIDUAL.value))
        raw_label = raw.get("label")
        if mode is ForEachMode.BATCH and raw_label is None:
            raise FlowValidationError(
                f"Step '{step_id}' for_each batch mode requires label"
            )
        if mode is ForEachMode.INDIVIDUAL and raw_label is not None:
            raise FlowValidationError(
                f"Step '{step_id}' for_each label is only valid in batch mode"
            )
        return ForEachDeclaration(
            source=self._reference_parser.parse(step_id, source),
            mode=mode,
            label=(
                self._expression_parser.parse(raw_label)
                if raw_label is not None
                else None
            ),
        )

    def _mode(self, step_id: str, raw: object) -> ForEachMode:
        try:
            return ForEachMode(raw)
        except (TypeError, ValueError) as error:
            raise FlowValidationError(
                f"Step '{step_id}' for_each mode must be individual or batch"
            ) from error
