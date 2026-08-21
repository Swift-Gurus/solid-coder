"""Defines searchable component metadata decoded from a plan."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: SearchPlanComponent
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries component terms that can seed a repository source search.
"""
class SearchPlanComponent(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    name: str = ""
    category: str = ""
    interfaces: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    stack: list[str] = Field(default_factory=list)
