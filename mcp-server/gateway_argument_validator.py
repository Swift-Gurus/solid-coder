"""Validates command-line arguments against resolved gateway tools."""

import inspect
import sys
from typing import Callable


"""
solid-name: GatewayArgumentValidator
solid-category: utility
solid-description: Validates command-line arguments accepted by a resolved gateway tool.
"""
class GatewayArgumentValidator:
    def validate(self, handler: Callable, tool_name: str, kwargs: dict) -> None:
        try:
            signature = inspect.signature(handler)
            parameters = signature.parameters.values()
            if any(
                parameter.kind == inspect.Parameter.VAR_KEYWORD
                for parameter in parameters
            ):
                return
            accepted = {
                parameter.name
                for parameter in parameters
                if parameter.kind
                in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                )
            }
            unknown = set(kwargs) - accepted
            if unknown:
                valid = ", ".join(sorted(accepted)) or "(none)"
                invalid = ", ".join(sorted(unknown))
                print(
                    f"Error: unknown argument(s) for '{tool_name}': {invalid}",
                    file=sys.stderr,
                )
                print(f"  Valid arguments: {valid}", file=sys.stderr)
                sys.exit(1)
        except (ValueError, TypeError):
            return
