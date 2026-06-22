"""
solid-description: Coordinates LLM execution and output handling to produce a violations list.
solid-category: service
solid-tags: [hook, llm]
"""

import sys
from pathlib import Path
_MCP_DIR = Path(__file__).resolve().parents[2]
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_MCP_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from typing import Optional, Protocol

from llm_executor import LLMExecuting
from file_based_output_handler import OutputHandling


class LLMReviewing(Protocol):
    def review(self, prompt: str, path: str, output_dir: Optional[str] = None) -> Optional[list]: ...


class LLMReviewer:
    """Coordination facade: protocol-typed executor + output_handler."""

    def __init__(self, executor: LLMExecuting, output_handler: OutputHandling) -> None:
        self._executor = executor
        self._output_handler = output_handler

    def review(self, prompt: str, path: str, output_dir: Optional[str] = None) -> Optional[list]:
        raw = self._executor.execute(prompt, path)
        return self._output_handler.handle(raw, path, output_dir)
