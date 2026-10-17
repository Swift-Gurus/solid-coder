"""
solid-description: Sends permission decisions for hook events with optional context or modifications.
solid-category: service
solid-tags: [hook]
"""

from typing import Optional

from gateway_output_writing import GatewayOutputWriting
from harness.pydantic_type_adapter_encoder import StructuredModelEncoding
from hook_decision import HookDecision
from hook_permission_response import HookPermissionResponse
from hook_permission_response_encoder import HookPermissionResponseEncoder
from process_exiting import ProcessExiting
from stdout_writer import StdoutWriter
from system_process_exit import SystemProcessExit


"""
solid-name: HookResponder
solid-category: service
solid-tags: [hook]
solid-description: Publishes final hook permission responses with context and corrected tool input.
"""
class HookResponder:
    """Sends Claude PreToolUse hook protocol responses."""

    def __init__(
        self,
        output: GatewayOutputWriting = StdoutWriter(),
        process: ProcessExiting = SystemProcessExit(),
        encoder: StructuredModelEncoding[HookPermissionResponse] = HookPermissionResponseEncoder(),
    ) -> None:
        self._output = output
        self._process = process
        self._encoder = encoder

    def _send(self, response: HookPermissionResponse) -> None:
        self._output.write_result(self._encoder.encode(response))
        self._process.exit(0)

    def allow(self, additional_context: str = "", updated_input: Optional[dict] = None) -> None:
        if updated_input is not None or additional_context:
            self._send(HookPermissionResponse(
                decision=HookDecision(additional_context=additional_context or None),
                updated_input=updated_input,
            ))
            return
        self._process.exit(0)

    def block(self, reason: str, additional_context: str = "") -> None:
        self._send(HookPermissionResponse(decision=HookDecision(
            allow=False,
            reason=reason,
            additional_context=additional_context or None,
        )))
