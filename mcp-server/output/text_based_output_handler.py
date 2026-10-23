"""
solid-description: Parses violations from the LLM's raw text response.
solid-category: service
solid-tags: [hook, llm]
"""

from response_parser import ResponseParsing


class TextBasedOutputHandler:
    """Output handler that parses violations from the LLM's raw text response."""

    def __init__(self, response_parser: ResponseParsing) -> None:
        self._response_parser = response_parser

    def handle(self, raw: str | None, path: str, output_dir: str | None) -> list | None:
        return self._response_parser.parse_response(raw, path)
