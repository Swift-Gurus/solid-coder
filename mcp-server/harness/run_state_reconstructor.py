"""
solid-description: Reconstructs execution state from a sequence of events.
solid-category: service
"""

from __future__ import annotations

from harness.models import RunState, StepOutputs


class RunStateReconstructor:
    """
    solid-description: Reconstructs execution state from a sequence of events.
    solid-category: service
    """

    def reconstruct(self, events: list[dict]) -> RunState:
        state: dict = {
            "completed": {},
            "running": [],
            "turn_count": 0,
            "status": "in_progress",
            "attempts_used": {},
            "rejection_reasons": {},
        }

        handlers = self._handlers()
        for event in events:
            handler = handlers.get(event.get("event"))
            if handler is not None:
                handler(state, event)

        return RunState(**state)

    def _handlers(self) -> dict:
        return {
            "step_started": self._on_step_started,
            "step_completed": self._on_step_completed,
            "turn_counted": self._on_turn_counted,
            "run_completed": self._on_run_completed,
            "run_timed_out": self._on_run_timed_out,
            "step_attempt_failed": self._on_attempt_failed,
            "step_rejected": self._on_step_rejected,
            "run_failed": self._on_run_failed,
        }

    def _on_step_started(self, state: dict, event: dict) -> None:
        step_id = event.get("step_id", event.get("instance_id", ""))
        if step_id and step_id not in state["running"]:
            state["running"].append(step_id)

    def _on_step_completed(self, state: dict, event: dict) -> None:
        step_id = event.get("step_id", event.get("instance_id", ""))
        state["completed"][step_id] = StepOutputs.from_dict(event.get("outputs") or {})
        if step_id in state["running"]:
            state["running"].remove(step_id)

    def _on_turn_counted(self, state: dict, event: dict) -> None:
        state["turn_count"] = event.get("total", state["turn_count"] + 1)

    def _on_run_completed(self, state: dict, event: dict) -> None:
        state["status"] = "done"

    def _on_run_timed_out(self, state: dict, event: dict) -> None:
        state["status"] = "timed_out"

    def _on_attempt_failed(self, state: dict, event: dict) -> None:
        step_id = event.get("step_id", "")
        state["attempts_used"][step_id] = state["attempts_used"].get(step_id, 0) + 1
        state["rejection_reasons"][step_id] = event.get("reason", "")

    def _on_step_rejected(self, state: dict, event: dict) -> None:
        self._on_attempt_failed(state, event)
        state["completed"].pop(event.get("step_id", ""), None)

    def _on_run_failed(self, state: dict, event: dict) -> None:
        state["status"] = "failed"
