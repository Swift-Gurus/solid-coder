"""
solid-description: Parses the LLM's raw text response into a structured violations list.
solid-category: service
solid-tags: [hook, llm]
"""

from pathlib import Path
from typing import Optional, Protocol

from hook_utils import Logging
from hc_violation_parser import ViolationParsing


class ResponseParsing(Protocol):
    def parse_response(self, raw: Optional[str], path: str) -> Optional[list]: ...


class ResponseParser:
    """Parses the LLM's raw text response into a violations list."""

    def __init__(self, parser: ViolationParsing, logger: Logging) -> None:
        self._parser = parser
        self._logger = logger

    def parse_response(self, raw: Optional[str], path: str) -> Optional[list]:
        if not raw:
            self._logger.log(f"HEALTH_ERR {Path(path).name}: bare session returned no result")
            raise RuntimeError(f"claude -p returned no result for {Path(path).name}")
        violations = self._parser.parse(raw)
        if violations is None:
            self._logger.log(
                f"HEALTH_ERR {Path(path).name}: parse_failed: raw[:100]={raw[:100]!r}"
            )
        return violations
