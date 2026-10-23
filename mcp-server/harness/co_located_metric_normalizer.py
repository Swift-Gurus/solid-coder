"""Expands typed co-located metrics into ordinary metric steps."""

from harness.co_located_metric_dependency_rebasing import (
    CoLocatedMetricDependencyRebasing,
)
from harness.co_located_metric_identity import CoLocatedMetricIdentity
from harness.co_located_metric_normalization import CoLocatedMetricNormalization
from harness.co_located_metric_normalizing import CoLocatedMetricNormalizing
from harness.co_located_metric_owner_validating import (
    CoLocatedMetricOwnerValidating,
)
from harness.co_located_metric_step_expanding import (
    CoLocatedMetricStepExpanding,
)
from harness.co_located_metrics_clearing import CoLocatedMetricsClearing
from harness.flow_validation_error import FlowValidationError
from harness.include_alias_group import IncludeAliasGroup
from harness.include_alias_group_members_appending import (
    IncludeAliasGroupMembersAppending,
)
from harness.include_group_membership_resolving import (
    IncludeGroupMembershipResolving,
)
from harness.step_declaration import StepDeclaration

"""
solid-name: CoLocatedMetricNormalizer
solid-category: service
solid-spec: [SPEC-058]
solid-description: Expands compact metric declarations while preserving root and included-workflow ownership.
"""


class CoLocatedMetricNormalizer(CoLocatedMetricNormalizing):
    def __init__(
        self,
        owner_validator: CoLocatedMetricOwnerValidating,
        membership_resolver: IncludeGroupMembershipResolving,
        step_expander: CoLocatedMetricStepExpanding,
        metrics_clearer: CoLocatedMetricsClearing,
        group_members_appender: IncludeAliasGroupMembersAppending,
        dependency_rebaser: CoLocatedMetricDependencyRebasing,
    ) -> None:
        self._owner_validator = owner_validator
        self._membership_resolver = membership_resolver
        self._step_expander = step_expander
        self._metrics_clearer = metrics_clearer
        self._group_members_appender = group_members_appender
        self._dependency_rebaser = dependency_rebaser

    def normalize(
        self,
        steps: list[StepDeclaration],
        alias_groups: list[IncludeAliasGroup],
        top_level_step_ids: set[str],
    ) -> CoLocatedMetricNormalization:
        normalized_steps: list[StepDeclaration] = []
        normalized_groups = list(alias_groups)
        normalized_top_level_ids = set(top_level_step_ids)
        metric_identities: list[CoLocatedMetricIdentity] = []

        for owner in steps:
            if not owner.co_located_metrics:
                normalized_steps.append(owner)
                continue

            owner_id = self._owner_validator.validate(owner)
            memberships = self._membership_resolver.resolve(
                owner_id,
                normalized_groups,
            )
            if len(memberships) > 1:
                raise FlowValidationError(
                    f"Step '{owner_id}' belongs to multiple workflow scopes "
                    "and cannot own co-located metrics"
                )
            owning_alias = next(iter(memberships), None)
            expansion = self._step_expander.expand(
                owner,
                owner_id,
                owning_alias,
            )
            normalized_steps.append(self._metrics_clearer.clear(owner))
            normalized_steps.extend(expansion.steps)
            metric_identities.extend(expansion.identities)

            if owning_alias is None:
                normalized_top_level_ids.update(expansion.step_ids)
                continue

            normalized_groups = [
                self._group_members_appender.append_members(
                    group,
                    expansion.step_ids,
                )
                if group.alias == owning_alias
                else group
                for group in normalized_groups
            ]

        return CoLocatedMetricNormalization(
            steps=self._dependency_rebaser.rebase(
                normalized_steps,
                metric_identities,
                normalized_groups,
            ),
            alias_groups=normalized_groups,
            top_level_step_ids=normalized_top_level_ids,
        )
