"""Validates included workflow output projections used by metrics."""

from harness.collection_metric_item_contract_validating import (
    CollectionMetricItemContractValidating,
)
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.include_alias_group import IncludeAliasGroup
from harness.models import StepDef
from harness.step_dependency_reachability_checking import (
    StepDependencyReachabilityChecking,
)
from harness.structured_model_decoding import StructuredModelDecoding
from harness.workflow_data_schema import WorkflowDataSchema
from harness.workflow_output_collection_validating import (
    WorkflowOutputCollectionValidating,
)
from harness.workflow_output_collection_validation_target import (
    WorkflowOutputCollectionValidationTarget,
)


"""
solid-name: WorkflowOutputCollectionValidator
solid-category: service
solid-spec: [SPEC-056]
solid-description: Resolves child output declarations and validates metric filters, reducers, and dependency coverage.
"""
class WorkflowOutputCollectionValidator(WorkflowOutputCollectionValidating):
    def __init__(
        self,
        reachability_checker: StepDependencyReachabilityChecking,
        item_contract_validator: CollectionMetricItemContractValidating,
        schema_decoder: StructuredModelDecoding[WorkflowDataSchema],
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._reachability_checker = reachability_checker
        self._item_contract_validator = item_contract_validator
        self._schema_decoder = schema_decoder
        self._error_factory = error_factory

    def validate(
        self,
        target: WorkflowOutputCollectionValidationTarget,
        steps: list[StepDef],
        alias_groups: list[IncludeAliasGroup],
    ) -> None:
        group = self._resolve_group(target, alias_groups)
        output = next(
            (
                declaration.specification
                for declaration in group.outputs
                if declaration.specification.name
                == target.source_reference.output_name
            ),
            None,
        )
        if output is None:
            raise self._error_factory.create(
                f"Step '{target.target_id}' scoring.source references unknown "
                f"output '{target.source_reference.output_name}' on workflow "
                f"'{target.source_reference.workflow_alias}'"
            )
        if not self._is_dependency(group, target.dependency_ids, steps):
            raise self._error_factory.create(
                f"Step '{target.target_id}' scoring.source must reference a "
                "transitive workflow dependency"
            )
        if output.schema is None:
            raise self._error_factory.create(
                f"Step '{target.target_id}' scoring.source workflow output "
                f"'{target.source_reference.output_name}' must declare a schema"
            )
        item_schema = self._schema_decoder.decode(
            output.schema,
            (
                f"workflow '{target.source_reference.workflow_alias}' output "
                "schema"
            ),
        )
        self._item_contract_validator.validate(
            target.target_id,
            item_schema,
            target.item_condition,
            target.metric_reducer,
        )

    def _resolve_group(
        self,
        target: WorkflowOutputCollectionValidationTarget,
        alias_groups: list[IncludeAliasGroup],
    ) -> IncludeAliasGroup:
        reference = target.source_reference.workflow_alias
        exact = next(
            (group for group in alias_groups if group.alias == reference),
            None,
        )
        if exact is not None:
            return exact
        scoped = [
            group
            for group in alias_groups
            if group.authored_alias == reference
            and (
                group.owner_alias is None
                or target.target_id.startswith(f"{group.owner_alias}.")
            )
        ]
        if len(scoped) == 1:
            return scoped[0]
        if not scoped:
            raise self._error_factory.create(
                f"Step '{target.target_id}' scoring.source references unknown "
                f"workflow '{reference}'"
            )
        raise self._error_factory.create(
            f"Step '{target.target_id}' scoring.source workflow reference "
            f"'{reference}' is ambiguous in this scope"
        )

    def _is_dependency(
        self,
        group: IncludeAliasGroup,
        dependency_ids: list[str],
        steps: list[StepDef],
    ) -> bool:
        if group.alias in dependency_ids:
            return True
        return bool(group.member_ids) and all(
            self._reachability_checker.is_dependency(
                member_id,
                dependency_ids,
                steps,
            )
            for member_id in group.member_ids
        )
