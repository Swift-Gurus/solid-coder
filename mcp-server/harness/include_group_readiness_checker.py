"""Checks whether a dynamic workflow include group may materialize."""

from harness.include_alias_group import IncludeAliasGroup
from harness.include_group_readiness_checking import IncludeGroupReadinessChecking
from harness.models import RunState
from harness.step_dependency_checking import StepDependencyChecking


"""
solid-name: IncludeGroupReadinessChecker
solid-category: service
solid-spec: [SPEC-037]
solid-description: Determines whether an included workflow's declared dependencies are terminal.
"""
class IncludeGroupReadinessChecker(IncludeGroupReadinessChecking):

    def __init__(self, dependency_checker: StepDependencyChecking) -> None:
        self._dependency_checker = dependency_checker

    def is_ready(
        self,
        group: IncludeAliasGroup,
        run_state: RunState,
    ) -> bool:
        return self._dependency_checker.dependencies_met(group, run_state)
