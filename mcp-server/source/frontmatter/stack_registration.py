"""Declares bounded syntax evidence for one metadata technology tag."""

from pydantic import BaseModel, ConfigDict, Field

"""
solid-name: StackRegistration
solid-category: model
solid-spec: [SPEC-069]
solid-description: Carries language extensions, optional module prerequisites and declaration signals for a registered stack tag.
"""


class StackRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tag: str
    file_extensions: list[str]
    modules: list[str] = Field(default_factory=list)
    signals: list[str]
