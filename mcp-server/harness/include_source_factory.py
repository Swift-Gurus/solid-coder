"""Constructs resolved include-source models."""

from __future__ import annotations

from harness.include_source import IncludeSource


"""
solid-name: IncludeSourceFactory
solid-category: factory
solid-spec: [SPEC-027, SPEC-035]
solid-description: Constructs the shared include-source representation from resolved location and provenance values.
"""
class IncludeSourceFactory:

    def create(
        self,
        alias: str,
        steps: list[dict],
        flow_path: str,
        identity: str | None = None,
        label: str | None = None,
        source_path: str | None = None,
        workflow_id: str | None = None,
    ) -> IncludeSource:
        return IncludeSource(
            alias=alias,
            steps=steps,
            flow_path=flow_path,
            identity=identity,
            label=label,
            source_path=source_path,
            workflow_id=workflow_id,
        )
