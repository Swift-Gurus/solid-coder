"""Defines resolved resource values attached to a workflow step."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.output_spec import OutputSpec


"""
solid-name: ResolvedStepResources
solid-category: model
solid-spec: [SPEC-027, SPEC-035]
solid-description: Represents prompt, script, and output resources attached to a workflow-step declaration.
"""
@dataclass
class ResolvedStepResources:
    prompt: object | None = None
    prompt_file: object | None = None
    script_file_reference: object | None = None
    script_file: object | None = None
    outputs: list[OutputSpec] = field(default_factory=list)
