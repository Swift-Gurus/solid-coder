"""Decodes compact metrics into typed deterministic metric contracts."""

from harness.co_located_metric_collection_decoding import (
    CoLocatedMetricCollectionDecoding,
)
from harness.co_located_metric_contract import CoLocatedMetricContract
from harness.co_located_metric_declaration import CoLocatedMetricDeclaration
from harness.collection_source_reference_parsing import (
    CollectionSourceReferenceParsing,
)
from harness.collection_metric_reducer_decoding import (
    CollectionMetricReducerDecoding,
)
from harness.condition_parsing import ConditionParsing
from harness.flow_validation_error import FlowValidationError
from harness.metric_declaration import MetricDeclaration
from harness.metric_scoring_declaration import MetricScoringDeclaration
from harness.metric_step_contract_assembling import MetricStepContractAssembling
from harness.output_spec import OutputSpec
from harness.step_output_reference import StepOutputReference
from harness.step_output_reference_syntax_error import (
    StepOutputReferenceSyntaxError,
)
from harness.structured_model_decoding import StructuredModelDecoding
from harness.workflow_expression_parsing import WorkflowExpressionParsing


"""
solid-name: CoLocatedMetricCollectionDecoder
solid-category: boundary-adapter
solid-spec: [SPEC-058]
solid-description: Decodes local-output measurements into validated conditions, reducers, severity bands, and source references.
"""
class CoLocatedMetricCollectionDecoder(CoLocatedMetricCollectionDecoding):
    def __init__(
        self,
        decoder: StructuredModelDecoding[CoLocatedMetricDeclaration],
        condition_parser: ConditionParsing,
        reducer_decoder: CollectionMetricReducerDecoding,
        contract_assembler: MetricStepContractAssembling,
        expression_parser: WorkflowExpressionParsing,
        source_reference_parser: CollectionSourceReferenceParsing,
    ) -> None:
        self._decoder = decoder
        self._condition_parser = condition_parser
        self._reducer_decoder = reducer_decoder
        self._contract_assembler = contract_assembler
        self._expression_parser = expression_parser
        self._source_reference_parser = source_reference_parser

    def decode(
        self,
        owner_step_id: str,
        outputs: list[OutputSpec],
        value: object,
    ) -> list[CoLocatedMetricContract]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise FlowValidationError(
                f"Step '{owner_step_id}' metrics must be an array"
            )
        contracts: list[CoLocatedMetricContract] = []
        for index, raw_declaration in enumerate(value):
            declaration = self._decoder.decode(
                raw_declaration,
                (
                    f"co-located metric {index + 1} on step "
                    f"'{owner_step_id}'"
                ),
            )
            source_name = declaration.scoring.source
            source_output = next(
                (output for output in outputs if output.name == source_name),
                None,
            )
            if source_output is None:
                self._raise_invalid_source(
                    owner_step_id,
                    declaration.id,
                    source_name,
                )
            if source_output.type != "data":
                raise FlowValidationError(
                    f"Co-located metric '{declaration.id}' on step "
                    f"'{owner_step_id}' must reference a data output; "
                    f"'{source_name}' is type '{source_output.type}'"
                )
            metric = MetricDeclaration(
                metric_id=declaration.metric_id,
                observation_id=declaration.observation_id,
                value=declaration.value,
                scoring=MetricScoringDeclaration(
                    minor=declaration.scoring.minor,
                    severe=declaration.scoring.severe,
                ),
            )
            reducer = self._reducer_decoder.decode(
                declaration.id,
                declaration.scoring.reducer,
                declaration.value.type,
                True,
            )
            condition = (
                self._condition_parser.parse(declaration.scoring.condition)
                if declaration.scoring.condition is not None
                else None
            )
            contracts.append(
                CoLocatedMetricContract(
                    id=declaration.id,
                    step_contract=self._contract_assembler.assemble(
                        metric=metric,
                        source=StepOutputReference(
                            step_id=owner_step_id,
                            output_name=source_name,
                        ),
                        condition=condition,
                        reducer=reducer,
                    ),
                )
            )
        return contracts

    def _raise_invalid_source(
        self,
        owner_step_id: str,
        metric_id: str,
        source_name: str,
    ) -> None:
        expression = self._expression_parser.parse(source_name)
        try:
            self._source_reference_parser.parse(expression.value)
        except StepOutputReferenceSyntaxError as error:
            raise FlowValidationError(
                f"Co-located metric '{metric_id}' on step "
                f"'{owner_step_id}' references undeclared local output "
                f"'{source_name}'"
            ) from error
        raise FlowValidationError(
            f"Co-located metric '{metric_id}' on step '{owner_step_id}' "
            "cannot reference another step or workflow; use an explicit "
            "'type: metric' step"
        )
