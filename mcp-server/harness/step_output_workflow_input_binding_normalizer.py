"""Normalizes one step-output workflow input binding."""

from harness.for_each_source_identity_resolving import (
    ForEachSourceIdentityResolving,
)
from harness.for_each_source_identity_scope import ForEachSourceIdentityScope
from harness.include_alias_group import IncludeAliasGroup
from harness.step_output_reference_parsing import StepOutputReferenceParsing
from harness.step_output_reference_syntax_error import (
    StepOutputReferenceSyntaxError,
)
from harness.workflow_expression import WorkflowExpression
from harness.workflow_input_binding import WorkflowInputBinding
from harness.workflow_input_binding_nested_normalizing import (
    WorkflowInputBindingNestedNormalizing,
)


"""
solid-name: StepOutputWorkflowInputBindingNormalizer
solid-category: service
solid-spec: [SPEC-035, SPEC-037]
solid-description: Normalizes one typed step-output input binding within its nested include scope.
"""
class StepOutputWorkflowInputBindingNormalizer(
    WorkflowInputBindingNestedNormalizing
):
    def __init__(
        self,
        reference_parser: StepOutputReferenceParsing,
        source_identity: ForEachSourceIdentityResolving,
    ) -> None:
        self._reference_parser = reference_parser
        self._source_identity = source_identity

    def normalize(
        self,
        binding: WorkflowInputBinding,
        group: IncludeAliasGroup,
        all_groups: list[IncludeAliasGroup],
    ) -> WorkflowInputBinding:
        try:
            reference = self._reference_parser.parse(
                binding.expression.value
            )
        except StepOutputReferenceSyntaxError:
            return binding
        owner_group = next(
            (
                candidate
                for candidate in all_groups
                if candidate.alias == group.owner_alias
            ),
            None,
        )
        if (
            owner_group is not None
            and f"{owner_group.alias}.{reference.step_id}"
            in owner_group.member_ids
        ):
            return binding
        source_id = self._source_identity.resolve(
            reference.step_id,
            ForEachSourceIdentityScope(
                member_ids=group.member_ids,
                excluded_aliases=[group.alias],
            ),
            all_groups,
        )
        return WorkflowInputBinding(
            name=binding.name,
            expression=WorkflowExpression(
                f"steps.{source_id}.outputs.{reference.output_name}"
            ),
        )
