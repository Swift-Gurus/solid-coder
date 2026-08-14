"""Coordinates one command-line gateway invocation."""

from typing import Callable

from gateway_argument_parsing import GatewayArgumentParsing
from gateway_argument_validating import GatewayArgumentValidating
from gateway_arguments_normalizing import GatewayArgumentsNormalizing
from gateway_tool_running import GatewayToolRunning
from logging_protocol import Logging
from process_exiting import ProcessExiting


"""
solid-name: GatewayApplication
solid-category: service
solid-description: Coordinates parsing, validation, and execution for one gateway command.
"""
class GatewayApplication:
    def __init__(
        self,
        parser: GatewayArgumentParsing,
        normalizer: GatewayArgumentsNormalizing,
        validator: GatewayArgumentValidating,
        runner: GatewayToolRunning,
        tools: dict[str, Callable],
        errors: Logging,
        process: ProcessExiting,
    ) -> None:
        self._parser = parser
        self._normalizer = normalizer
        self._validator = validator
        self._runner = runner
        self._tools = tools
        self._errors = errors
        self._process = process

    def run(self, arguments: list[str]) -> None:
        parsed = self._normalizer.normalize(self._parser.parse(arguments))
        tool_name = parsed.tool_name
        if tool_name is None or tool_name in ("-h", "--help", "help"):
            self._errors.log("Usage: python3 gateway.py <tool-name> [--arg value ...]")
            self._errors.log(f"Available tools: {', '.join(sorted(self._tools))}")
            self._process.exit(1 if tool_name is None else 0)
            return
        handler = self._tools.get(tool_name)
        if handler is None:
            self._errors.log(f"Error: unknown tool '{tool_name}'")
            self._errors.log(f"Available: {', '.join(sorted(self._tools))}")
            self._process.exit(1)
            return
        self._validator.validate(handler, tool_name, parsed.values)
        self._runner.run(handler, tool_name, parsed.values)
