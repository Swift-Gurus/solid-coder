"""
solid-name: FlowEngineConfig
solid-category: model
solid-spec: [SPEC-027]
solid-description: Provides validated configuration for the flow engine's script step executable allowlist.
"""

from pydantic import BaseModel, ConfigDict, Field


class FlowEngineConfig(BaseModel):
    """[flow_engine] section — permitted executables for engine-run script steps."""

    model_config = ConfigDict(extra="forbid")

    permitted_executables: list[str] = Field(default_factory=list)
