"""Defines searchable implementation-plan item metadata."""

from pydantic import BaseModel, ConfigDict


"""
solid-name: SearchPlanItem
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries a component identifier that can seed a repository source search.
"""
class SearchPlanItem(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    component: str = ""
