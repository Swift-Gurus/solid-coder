"""Resolves registered source-search target construction policy."""

from harness.flow_validation_error import FlowValidationError
from source.search_target_granularity import SearchTargetGranularity
from source.source_search_targets_builder_registration import (
    SourceSearchTargetsBuilderRegistration,
)
from source.source_search_targets_building import SourceSearchTargetsBuilding
from source.source_search_targets_building_resolving import (
    SourceSearchTargetsBuildingResolving,
)


"""
solid-name: SourceSearchTargetsBuilderResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Resolves registered search-target construction behavior without hardcoded granularity branches.
"""
class SourceSearchTargetsBuilderResolver(
    SourceSearchTargetsBuildingResolving
):
    def __init__(
        self,
        registrations: list[SourceSearchTargetsBuilderRegistration],
    ) -> None:
        self._registrations = registrations

    def resolve(
        self,
        granularity: SearchTargetGranularity,
    ) -> SourceSearchTargetsBuilding:
        for registration in self._registrations:
            if registration.granularity is granularity:
                return registration.builder
        raise FlowValidationError(
            f"No source-search target builder for '{granularity.value}'"
        )
