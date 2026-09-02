"""Carries one runtime-rebased include group and its step templates."""

from dataclasses import dataclass

from harness.include_alias_group import IncludeAliasGroup
from harness.models import StepDef


"""
solid-name: IncludeGroupRuntime
solid-category: model
solid-spec: [SPEC-037]
solid-description: Carries a runtime-qualified nested include group with the templates owned by that exact parent instance.
"""
@dataclass(frozen=True)
class IncludeGroupRuntime:
    group: IncludeAliasGroup
    templates: list[StepDef]
