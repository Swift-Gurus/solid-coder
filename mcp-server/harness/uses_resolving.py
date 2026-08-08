"""Defines resolution of reusable workflow step fragments."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: UsesResolving
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-035]
solid-description: Contract for resolving a reusable step fragment into one raw workflow step.
"""
class UsesResolving(Protocol):
    def resolve(self, raw_step: dict, flow_path: str, search_paths: list[str]) -> dict: ...
