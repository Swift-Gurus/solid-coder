from typing import Protocol

from harness.collection_source_reference_parsing import CollectionSourceReferenceParsing
from harness.flow_validation_error import FlowValidationError
from harness.output_spec import OutputSpec
from harness.step_output_reference_syntax_error import StepOutputReferenceSyntaxError
from harness.workflow_expression_parsing import WorkflowExpressionParsing

"""
solid-name: CoLocatedMetricSourceValidating
solid-category: abstraction
solid-spec: [SPEC-058]
solid-description: Contract for validating local metric output ownership and explaining invalid source references.
"""


class CoLocatedMetricSourceValidating(Protocol):
    def validate(
        self, owner_id: str, metric_id: str, source: str, outputs: list[OutputSpec]
    ) -> None: ...


"""
solid-name: CoLocatedMetricSourceValidator
solid-category: service
solid-spec: [SPEC-058]
solid-description: Validates local metric output references and distinguishes undeclared sources from unsupported cross-step references.
"""


class CoLocatedMetricSourceValidator(CoLocatedMetricSourceValidating):
    def __init__(
        self,
        expression_parser: WorkflowExpressionParsing,
        reference_parser: CollectionSourceReferenceParsing,
    ) -> None:
        self._expression_parser = expression_parser
        self._reference_parser = reference_parser

    def validate(
        self, owner_id: str, metric_id: str, source: str, outputs: list[OutputSpec]
    ) -> None:
        output = next(
            (candidate for candidate in outputs if candidate.name == source), None
        )
        if output is not None:
            if output.type != "data":
                raise FlowValidationError(
                    f"Co-located metric '{metric_id}' on step '{owner_id}' must reference a data output; '{source}' is type '{output.type}'"
                )
            return
        expression = self._expression_parser.parse(source)
        try:
            self._reference_parser.parse(expression.value)
        except StepOutputReferenceSyntaxError as error:
            raise FlowValidationError(
                f"Co-located metric '{metric_id}' on step '{owner_id}' references undeclared local output '{source}'"
            ) from error
        raise FlowValidationError(
            f"Co-located metric '{metric_id}' on step '{owner_id}' cannot reference another step or workflow; use an explicit 'type: metric' step"
        )
