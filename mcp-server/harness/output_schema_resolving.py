"""
solid-name: OutputSchemaResolving
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for resolving schema references within a step.
"""

from __future__ import annotations

from typing import Protocol


class OutputSchemaResolving(Protocol):

    def resolve(self, step: dict, flow_file_path: str) -> dict: ...
