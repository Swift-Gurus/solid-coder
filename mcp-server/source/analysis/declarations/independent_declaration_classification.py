from typing import Literal

from findings.metric_additional_info import MetricAdditionalInfo
from pydantic import BaseModel, ConfigDict, Field, StrictBool

"""
solid-name: IndependentDeclarationClassification
solid-category: model
solid-spec: [SPEC-066]
solid-description: Records evidenced business-behavior classification for a declaration with no semantic grouping association.
"""


class IndependentDeclarationClassification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["independent"]
    declaration_id: str = Field(min_length=1)
    has_business_logic: StrictBool
    additional_info: MetricAdditionalInfo
