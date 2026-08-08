"""Defines resolution of a raw workflow document."""

from typing import Protocol

from harness.flow_def import FlowDef


"""
solid-name: FlowDefinitionResolving
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-035]
solid-description: Contract for resolving workflow composition and file-backed resources before validation.
"""
class FlowDefinitionResolving(Protocol):

    def resolve(self, raw: dict, path: str, search_paths: list[str]) -> FlowDef:
        ...
