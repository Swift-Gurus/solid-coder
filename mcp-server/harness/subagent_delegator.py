"""
solid-name: SubagentDelegator
solid-category: service
solid-spec: [SPEC-013]
solid-description: Prepares execution bodies for subagent delegation when required by execution parameters.
"""

from __future__ import annotations

from harness.delegate_instruction_builder import DelegateInstructionBuilder
from harness.delegate_instruction_building import DelegateInstructionBuilding
from harness.subagent_delegating import SubagentDelegating

_SUBAGENT_MODE = "subagent"


class SubagentDelegator(SubagentDelegating):

    def __init__(self, delegate_instruction_builder: DelegateInstructionBuilding | None = None) -> None:
        self._delegate_instruction_builder = delegate_instruction_builder or DelegateInstructionBuilder()

    def wrap_if_subagent(self, body: str, execution: dict) -> str:
        if execution.get("mode") != _SUBAGENT_MODE:
            return body
        instruction = self._delegate_instruction_builder.build(body)
        return f"Launch a subagent with the following prompt:\n\n{instruction}"
