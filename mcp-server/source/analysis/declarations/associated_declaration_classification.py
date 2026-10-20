from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from findings.metric_additional_info import MetricAdditionalInfo


"""
solid-name: AssociatedDeclarationClassification
solid-category: model
solid-spec: [SPEC-066]
solid-description: Records an evidenced semantic relationship from one declaration to an independently classified implementation or contract.
"""
class AssociatedDeclarationClassification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["implemented_contract", "supporting_helper", "cohesive_contract"]
    declaration_id: str = Field(min_length=1)
    related_declaration_id: str = Field(min_length=1)
    additional_info: MetricAdditionalInfo
