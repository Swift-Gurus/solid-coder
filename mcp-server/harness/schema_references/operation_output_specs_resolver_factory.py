from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.pydantic_operation_output_specs_resolver import (
    PydanticOperationOutputSpecsResolver,
)
from harness.schema_references.referencing_json_schema_expander import (
    ReferencingJsonSchemaExpander,
)
from harness.schema_references.referencing_schema_registry_factory import (
    ReferencingSchemaRegistryFactory,
)
from harness.workflow_data_schema import WorkflowDataSchema
from referencing import Registry
from referencing.jsonschema import DRAFT202012

"""
solid-name: OperationOutputSpecsResolverFactory
solid-category: factory
solid-spec: [SPEC-057]
solid-description: Provides typed operation-output contracts with addressable nested fields and retained recursive schema references.
"""


class OperationOutputSpecsResolverFactory:
    def make(
        self, error_factory: FlowValidationErrorCreating
    ) -> PydanticOperationOutputSpecsResolver:
        return PydanticOperationOutputSpecsResolver(
            error_factory=error_factory,
            schema_expander=ReferencingJsonSchemaExpander(
                registries=ReferencingSchemaRegistryFactory(
                    registry=Registry(), specification=DRAFT202012
                ),
                error_factory=error_factory,
            ),
            schema_decoder=PydanticModelDecoder(WorkflowDataSchema),
        )
