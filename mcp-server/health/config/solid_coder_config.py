"""
solid-description: Provides unified configuration for all system subsystems.
solid-category: model
"""

import sys
from pathlib import Path

_MODULE_DIR = Path(__file__).resolve().parent
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

from pydantic import BaseModel, ConfigDict, Field

from hook_config import HookConfig
from inference_config import InferenceConfig
from llm_config import LlmConfig
from server_config import ServerConfig


class SolidCoderConfig(BaseModel):
    """Root config model — one section field per top-level TOML table."""

    model_config = ConfigDict(extra="forbid")

    llm: LlmConfig = Field(default_factory=LlmConfig)
    hooks: dict[str, HookConfig] = Field(default_factory=dict)
    inference: InferenceConfig = Field(default_factory=InferenceConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    code_review_on_write_enabled: bool = Field(default=False)

    def hook_exclude(self, hook: str) -> list:
        """Return the exclude glob patterns configured for a named hook."""
        cfg = self.hooks.get(hook)
        return cfg.exclude if cfg is not None else []
