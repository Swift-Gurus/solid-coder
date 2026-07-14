"""
solid-description: Encapsulates inference generation parameters for the local LLM server.
solid-category: model
"""

from pydantic import BaseModel, ConfigDict


class InferenceConfig(BaseModel):
    """[inference] section — per-request generation params sent to the local LLM server."""

    model_config = ConfigDict(extra="forbid")

    temperature: float = 0
    top_k: int = 20
    top_p: float = 0.95
    min_p: float = 0.05
    repeat_penalty: float = 1.1
    max_tokens: int = 4096
