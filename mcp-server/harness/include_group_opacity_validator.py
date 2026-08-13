"""Validates include-group dependency opacity."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.graph_step_field_reading import GraphStepFieldReading
from harness.include_alias_group import IncludeAliasGroup
from harness.include_group_membership_resolving import IncludeGroupMembershipResolving
from harness.include_group_opacity_validating import IncludeGroupOpacityValidating


"""
solid-name: IncludeGroupOpacityValidator
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Rejects dependencies that cross unrelated include-group boundaries.
"""
class IncludeGroupOpacityValidator(IncludeGroupOpacityValidating):

    def __init__(
        self,
        membership_resolver: IncludeGroupMembershipResolving,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._membership_resolver = membership_resolver
        self._error_factory = error_factory

    def validate(
        self,
        steps: list[GraphStepFieldReading],
        alias_groups: list[IncludeAliasGroup],
    ) -> None:
        for step in steps:
            step_id = step.id
            step_memberships = self._membership_resolver.resolve(
                step_id,
                alias_groups,
            )
            for dependency in step.depends_on or []:
                dependency_memberships = self._membership_resolver.resolve(
                    dependency,
                    alias_groups,
                )
                if dependency_memberships and step_memberships.isdisjoint(
                    dependency_memberships
                ):
                    dependency_alias = max(dependency_memberships, key=len)
                    raise self._error_factory.create(
                        f"Step '{step_id}' may not depend on qualified reference "
                        f"'{dependency}' from outside group '{dependency_alias}'"
                    )
