"""
solid-description: Configuration for LLM backend selection and request timeout control.
solid-category: model
"""

from pydantic import BaseModel, ConfigDict


class LlmConfig(BaseModel):
    """[llm] section — which backend the pre-write health-check gate talks to.

    `timeout` is the single configured value for every subprocess call this
    gate makes — the LLM session (claude -p / codex exec) and the gateway
    CLI calls (get_candidate_tags, load_detection_rules, ...) alike.
    """

    model_config = ConfigDict(extra="forbid")

    backend: str = "claude"
    host: str = "http://localhost:8080"
    model: str = "local"
    timeout: int = 300
    debug: bool = False
    codex_home: str = ""
    bare_session_model: str = ""
