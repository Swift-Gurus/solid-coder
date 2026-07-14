"""
solid-description: Specifies paths that bypass a named hook.
solid-category: model
"""

from pydantic import BaseModel, ConfigDict, Field


class HookConfig(BaseModel):
    """[hooks.<name>] section — paths that bypass the named hook."""

    model_config = ConfigDict(extra="forbid")

    exclude: list = Field(default_factory=list)
