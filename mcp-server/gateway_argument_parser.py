"""Parses gateway command-line arguments."""

from pydantic import TypeAdapter

from gateway_argument_parsing import GatewayArgumentParsing
from gateway_arguments import GatewayArguments


"""
solid-name: GatewayArgumentParser
solid-category: boundary-adapter
solid-description: Parses a gateway tool name and its command-line argument values.
"""
class GatewayArgumentParser(GatewayArgumentParsing):
    def __init__(self, arguments_adapter: TypeAdapter) -> None:
        self._arguments_adapter = arguments_adapter

    def parse(self, arguments: list[str]) -> GatewayArguments:
        tool_name = arguments[1] if len(arguments) >= 2 else None
        values: dict = {}
        index = 2
        while index < len(arguments):
            argument = arguments[index]
            if argument.startswith("--"):
                key = argument[2:].replace("-", "_")
                if index + 1 < len(arguments) and not arguments[index + 1].startswith("--"):
                    value = arguments[index + 1]
                    values[key] = (
                        [item.strip() for item in value.split(",")]
                        if "," in value
                        else value
                    )
                    index += 2
                else:
                    values[key] = True
                    index += 1
                continue
            values.setdefault("args", []).append(argument)
            index += 1
        return self._arguments_adapter.validate_python(
            {"tool_name": tool_name, "values": values}
        )
