"""Defines searchable metadata decoded from architecture and implementation plans."""

from pydantic import BaseModel, ConfigDict, Field

from search.search_plan_component import SearchPlanComponent
from search.search_plan_item import SearchPlanItem


"""
solid-name: SearchPlanDocument
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries plan metadata that can seed repository source-search queries.
"""
class SearchPlanDocument(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    components: list[SearchPlanComponent] = Field(default_factory=list)
    plan_items: list[SearchPlanItem] = Field(default_factory=list)
    spec_number: str = ""
