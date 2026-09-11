"""Defines one model-facing compiled aggregate turn."""

from dataclasses import dataclass, field


"""
solid-name: CompiledAggregateTurn
solid-category: model
solid-spec: [SPEC-045]
solid-description: Carries the compact aggregate prompt and its exact submission schema.
"""
@dataclass(frozen=True)
class CompiledAggregateTurn:
    prompt: str
    schema: dict[str, object] = field(default_factory=dict)
