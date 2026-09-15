"""
solid-name: FeatureFlagsConfig
solid-category: model
solid-description: Supplies feature flag settings that control experimental behaviors.
"""

from pydantic import BaseModel, ConfigDict, Field

from health_check_mode import HealthCheckMode


class FeatureFlagsConfig(BaseModel):
    """[feature_flags] section — toggles for experimental/opt-in behaviors."""

    model_config = ConfigDict(extra="forbid")

    flow_plain_text_response: bool = Field(default=True)
    health_check_mode: HealthCheckMode = HealthCheckMode.WORKFLOW
