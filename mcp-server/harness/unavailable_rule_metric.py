from typing import Literal

from findings.metric_additional_info import MetricAdditionalInfo
from pydantic import BaseModel, ConfigDict

"""
solid-name: UnavailableRuleMetric
solid-category: model
solid-spec: [SPEC-057]
solid-description: Records an identified metric whose evidence does not permit measurement, without inventing a value or severity.
"""


class UnavailableRuleMetric(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_id: str
    observation_id: str
    status: Literal["unavailable"] = "unavailable"
    additional_info: MetricAdditionalInfo
