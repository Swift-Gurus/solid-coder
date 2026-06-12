"""
solid-description: Parses violations from the LLM's raw text response.
solid-category: service
solid-tags: [hook, llm]
"""

from typing import Optional

from file_based_output_handler import OutputHandling
from response_parser import ResponseParsing


class TextBasedOutputHandler:
    """Output handler that parses violations from the LLM's raw text response."""

    def __init__(self, response_parser: ResponseParsing) -> None:
        self._response_parser = response_parser

    def handle(self, raw: Optional[str], path: str, output_dir: Optional[str]) -> Optional[list]:
        return self._response_parser.parse_response(raw, path)
