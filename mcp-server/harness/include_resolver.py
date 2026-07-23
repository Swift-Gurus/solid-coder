"""
solid-name: IncludeResolver
solid-category: service
solid-spec: [SPEC-027]
solid-description: Resolves include and group directives while detecting circular includes.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

from harness.include_resolution import IncludeResolution
from harness.include_resolving import IncludeResolving
from harness.models import FlowValidationError
from scoring.yaml_config_file_loader import ConfigFileLoading


class CircularIncludeDetecting(Protocol):
    def check(self, resolved_path: str, ancestors: list[str]) -> None: ...


class CircularIncludeGuard:

    def check(self, resolved_path: str, ancestors: list[str]) -> None:
        if resolved_path in ancestors:
            raise FlowValidationError(
                f"Circular include detected: {' -> '.join(ancestors + [resolved_path])}"
            )


class IncludeResolver(IncludeResolving):

    def __init__(
        self,
        file_loader: ConfigFileLoading,
        circular_guard: CircularIncludeDetecting | None = None,
    ) -> None:
        self._file_loader = file_loader
        self._circular_guard = circular_guard or CircularIncludeGuard()

    def resolve(self, raw_steps: list[dict], flow_file_path: str) -> IncludeResolution:
        root = str(Path(os.path.abspath(flow_file_path)))
        return self._resolve(raw_steps, flow_file_path, ancestors=[root])

    def _resolve(self, raw_steps: list[dict], flow_file_path: str, ancestors: list[str]) -> IncludeResolution:
        expanded_steps: list[dict] = []
        alias_groups: dict[str, list[str]] = {}
        include_chain: list[str] = list(ancestors)

        for entry in raw_steps:
            source = self._group_source(entry, flow_file_path, ancestors)
            if source is None:
                expanded_steps.append(entry)
                continue

            alias, raw_group_steps, group_flow_path, group_ancestors = source
            nested = self._resolve(raw_group_steps, group_flow_path, group_ancestors)
            original_ids = {step["id"] for step in nested.steps}
            qualified_steps = [self._qualify(step, alias, original_ids) for step in nested.steps]
            group_members = [f"{alias}.{sid}" for sid in original_ids]

            expanded_steps.extend(qualified_steps)
            alias_groups[alias] = group_members
            for nested_alias, nested_members in nested.alias_groups.items():
                alias_groups.setdefault(nested_alias, nested_members)
            for chain_entry in nested.include_chain:
                if chain_entry not in include_chain:
                    include_chain.append(chain_entry)

        return IncludeResolution(steps=expanded_steps, alias_groups=alias_groups, include_chain=include_chain)

    def _group_source(
        self, entry: dict, flow_file_path: str, ancestors: list[str]
    ) -> tuple[str, list[dict], str, list[str]] | None:
        include_path = entry.get("include")
        if include_path is not None:
            resolved_path = str(Path(os.path.abspath(flow_file_path)).parent / include_path)
            self._circular_guard.check(resolved_path, ancestors)
            raw = self._file_loader.load(Path(resolved_path))
            if raw is None:
                raise FlowValidationError(
                    f"Unresolvable include: '{include_path}' not found relative to '{flow_file_path}'"
                )
            return entry["as"], raw.get("steps") or [], resolved_path, ancestors + [resolved_path]

        group_alias = entry.get("group")
        if group_alias is not None:
            inline_steps = entry.get("steps") or []
            if not inline_steps:
                raise FlowValidationError(f"Group '{group_alias}' must declare a non-empty 'steps' list")
            return group_alias, inline_steps, flow_file_path, ancestors

        return None

    def _qualify(self, step: dict, alias: str, sibling_ids: set[str]) -> dict:
        qualified = dict(step)
        qualified["id"] = f"{alias}.{step['id']}"
        qualified["depends_on"] = [
            f"{alias}.{dep}" if dep in sibling_ids else dep
            for dep in (step.get("depends_on") or [])
        ]
        return qualified
