"""
solid-name: ExecutionIntentResolver
solid-category: service
solid-spec: [SPEC-013]
solid-description: Resolves the execution mode for a given intent and environment.
"""

from __future__ import annotations

from harness.execution_intent_resolving import ExecutionIntentResolving

_ISOLATED_INTENTS = {"parallel_isolated", "sequential_isolated"}


class ExecutionIntentResolver:

    def resolve(self, intent: str, detected_env: str) -> dict:
        if intent == "inline":
            return {"mode": "inline"}
        if intent in _ISOLATED_INTENTS:
            mode = "subagent" if detected_env == "claude-code" else "session"
            return {"mode": mode}
        return {"mode": "inline"}
