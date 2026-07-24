"""
solid-name: delegate_instruction_building
solid-category: service
solid-spec: [SPEC-027]
solid-description: Enriches a prompt with execution instructions for a delegate step.
"""

from __future__ import annotations

_ISOLATION_HINT = (
    "When calling flow_start for this, pass isolated=true. After starting, keep calling "
    "flow_next until the flow reports done, failed, or timed out."
)


def build_delegate_instruction(prompt: str) -> str:
    return f"{prompt}\n\n{_ISOLATION_HINT}"
