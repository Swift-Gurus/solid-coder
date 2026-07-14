"""
solid-description: Validates and enforces a typed structure for local LLM server configuration.
solid-category: model
"""

from pydantic import BaseModel, ConfigDict


class ServerConfig(BaseModel):
    """[server] section — settings for scripts/run-local-llm.sh. Not read by Python."""

    model_config = ConfigDict(extra="forbid")

    model: str = ""
    port: int = 8080
    ctx_size: int = 65536
    gpu_layers: int = 99
    parallel: int = 1
    batch_size: int = 2048
    ubatch_size: int = 512
    mlock: bool = True
    seed: int = 42
    reasoning: str = "auto"
