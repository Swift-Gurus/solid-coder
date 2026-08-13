"""Carries the context required to traverse one workflow include source."""

from dataclasses import dataclass


"""
solid-name: IncludeTraversalContext
solid-category: model
solid-spec: [SPEC-027, SPEC-035]
solid-description: Carries a workflow path and its include ancestry during recursive traversal.
"""
@dataclass(frozen=True)
class IncludeTraversalContext:
    flow_file_path: str
    ancestor_identities: list[str]
    ancestor_labels: list[str]
