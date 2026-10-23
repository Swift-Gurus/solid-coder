"""Executes resolved gateway tools for command-line clients."""

from collections.abc import Callable

from gateway_output_writing import GatewayOutputWriting
from logging_protocol import Logging
from process_exiting import ProcessExiting

"""
solid-name: GatewayToolRunner
solid-category: utility
solid-description: Runs a selected tool and reports its outcome to the caller.
"""


class GatewayToolRunner:
    def __init__(
        self,
        output: GatewayOutputWriting,
        errors: Logging,
        process: ProcessExiting,
    ) -> None:
        self._output = output
        self._errors = errors
        self._process = process

    def run(self, handler: Callable, tool_name: str, kwargs: dict) -> None:
        try:
            result = handler(**kwargs)
            if isinstance(result, dict) and result.get("errors"):
                for error in result["errors"]:
                    self._errors.log(f"Error: {error.get('error', 'unknown error')}")
                self._process.exit(1)
                return
            if isinstance(result, str) and result.startswith("Error:"):
                self._errors.log(result)
                self._process.exit(1)
                return
            self._output.write_result(result)
        except TypeError as error:
            self._errors.log(f"Error: bad arguments for '{tool_name}': {error}")
            self._process.exit(1)
        except Exception as error:  # noqa: BLE001 — CLI boundary reports tool failures with exit status 1.
            self._errors.log(f"Error: {error}")
            self._process.exit(1)
