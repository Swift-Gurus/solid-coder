"""Composes validation for authored collection source references."""

from harness.collection_metric_item_contract_validator import (
    CollectionMetricItemContractValidator,
)
from harness.condition_item_schema_validator import ConditionItemSchemaValidator
from harness.condition_reference_collector import ConditionReferenceCollector
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.for_each_collection_validator import ForEachCollectionValidator
from harness.for_each_reference_validator import ForEachReferenceValidator
from harness.for_each_source_identity_resolver import ForEachSourceIdentityResolver
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.step_dependency_reachability_checker import (
    StepDependencyReachabilityChecker,
)
from harness.workflow_data_schema import WorkflowDataSchema
from harness.workflow_output_collection_validator import (
    WorkflowOutputCollectionValidator,
)


"""
solid-name: CollectionReferenceValidatorFactory
solid-category: factory
solid-spec: [SPEC-030, SPEC-053, SPEC-056]
solid-description: Composes shared item-schema validation for step-output iteration and workflow-output metric sources.
"""
class CollectionReferenceValidatorFactory:
    def make(
        self,
        error_factory: FlowValidationErrorCreating,
    ) -> ForEachCollectionValidator:
        reachability_checker = StepDependencyReachabilityChecker()
        schema_decoder = PydanticModelDecoder(
            model_type=WorkflowDataSchema,
        )
        item_contract_validator = CollectionMetricItemContractValidator(
            item_schema_validator=ConditionItemSchemaValidator(
                reference_collector=ConditionReferenceCollector(),
                error_factory=error_factory,
            )
        )
        return ForEachCollectionValidator(
            target_validator=ForEachReferenceValidator(
                reachability_checker=reachability_checker,
                item_contract_validator=item_contract_validator,
                schema_decoder=schema_decoder,
                error_factory=error_factory,
            ),
            workflow_output_validator=WorkflowOutputCollectionValidator(
                reachability_checker=reachability_checker,
                item_contract_validator=item_contract_validator,
                schema_decoder=schema_decoder,
                error_factory=error_factory,
            ),
            source_identity_resolver=ForEachSourceIdentityResolver(),
        )
