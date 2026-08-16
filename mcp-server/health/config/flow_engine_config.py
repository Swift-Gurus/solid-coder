"""Defines validated flow-engine configuration."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: FlowEngineConfig
solid-category: model
solid-spec: [SPEC-027, SPEC-037]
solid-description: Provides validated process permissions and bounded session execution configuration.
"""
class FlowEngineConfig(BaseModel):
    """[flow_engine] section — process permissions and bounded session execution."""

    model_config = ConfigDict(extra="forbid")

    permitted_executables: list[str] = Field(default_factory=list)
    max_parallel_sessions: int = Field(default=4, ge=1)
