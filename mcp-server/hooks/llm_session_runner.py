"""
solid-description: Executes a prompt through an injected runner and returns the corrected content.
solid-category: service
solid-tags: [hook]
"""

from typing import Callable, Optional

from config_provider import ConfigProvider
from hook_utils import StrValidator, parse_json_field


class LlmSessionRunner:
    """Runs a prompt through an injected LLM runner factory and extracts corrected_content."""

    def __init__(self, runner_factory: Callable, config_provider: ConfigProvider) -> None:
        self._runner_factory = runner_factory
        self._config_provider = config_provider

    def run(self, prompt: str, cwd: str = "") -> Optional[str]:
        runner = self._runner_factory(mcp_config="", allowed_tools="", cwd=cwd)
        raw = runner.run(prompt, timeout=self._config_provider.load_timeout())
        return parse_json_field(raw, "corrected_content", StrValidator())