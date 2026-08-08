"""Defines assembly of an executable workflow definition."""

from typing import Protocol

from harness.flow_def import FlowDef


"""
solid-name: FlowDefinitionAssembling
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-035]
solid-description: Contract for assembling a resolved workflow into its immutable executable model.
"""
class FlowDefinitionAssembling(Protocol):

    def assemble(self, definition: FlowDef) -> FlowDef:
        ...
