"""
solid-description: Provides validated configuration for LLM backend selection and request timeout control.
solid-category: model
"""

from pydantic import BaseModel, ConfigDict


class LlmConfig(BaseModel):
    """[llm] section — which backend the pre-write health-check gate talks to."""

    model_config = ConfigDict(extra="forbid")

    backend: str = "claude"
    host: str = "http://localhost:8080"
    model: str = "local"
    timeout: int = 300
    bare_session_timeout: int = 300
    debug: bool = False
    codex_home: str = ""
    bare_session_model: str = ""
