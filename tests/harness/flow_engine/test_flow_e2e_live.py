"""
solid-name: test_flow_e2e_live
solid-category: integration-test
solid-spec: [SPEC-013, SPEC-027]
solid-description: Runs the e2e_test flow to completion via a real spawned Claude Code
session driving flow_start/flow_next, then verifies the resulting event log shows the
expected transitions — script-step auto-run, aliased group completion, and a clean done.

Not part of the fast unit-test sweep — spawns a real LLM session. Run explicitly:
    python3 tests/harness/flow_engine/test_flow_e2e_live.py
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

_MCP_SERVER = Path(__file__).resolve().parents[3] / "mcp-server"
_MCP_HEALTH_CONFIG = _MCP_SERVER / "health" / "config"
for _d in (_MCP_SERVER, _MCP_HEALTH_CONFIG):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hook_utils import run_claude_bare, solid_coder_project_dir  # noqa: E402
from mcp_config_builder import build_mcp_config  # noqa: E402

_PROJECT_ROOT = _MCP_SERVER.parent
_ALLOWED_TOOLS = "mcp__pipeline__flow_start,mcp__pipeline__flow_next,mcp__pipeline__flow_status"

# Forced by the flow's DAG (see e2e_test.yaml / e2e_review_group.yaml): check_environment auto-runs
# the instant greet completes, before the agent is ever offered count_words; draft_review gates on
# both count_words and check_environment; approve_review gates on draft_review; summarize gates on
# all three branches. So completion order is fully determined, not just membership.
_EXPECTED_STEP_SEQUENCE = [
    "greet",
    "check_environment",
    "count_words",
    "review.draft_review",
    "review.approve_review",
    "summarize",
]


def _build_prompt(flow_name: str, parent_session_id: str) -> str:
    header = f"# spawned-by: {parent_session_id}\n\n" if parent_session_id else ""
    return (
        f"{header}"
        f'Call flow_start with flow="{flow_name}".'
    )


class TestFlowE2ELive(unittest.TestCase):

    TIMEOUT = 300

    def test_e2e_test_flow_reaches_done_with_expected_transitions(self):
        runs_dir = solid_coder_project_dir(_PROJECT_ROOT) / "runs"
        before = set(runs_dir.glob("*/events.jsonl")) if runs_dir.exists() else set()

        parent_session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        run_claude_bare(
            prompt=_build_prompt("e2e_test", parent_session_id),
            allowed_tools=_ALLOWED_TOOLS,
            mcp_config=build_mcp_config(_PROJECT_ROOT),
            timeout=self.TIMEOUT,
            cwd=str(_PROJECT_ROOT),
        )

        after = set(runs_dir.glob("*/events.jsonl")) if runs_dir.exists() else set()
        new_logs = after - before
        self.assertTrue(new_logs, "No new events.jsonl appeared after the session")
        events_path = max(new_logs, key=lambda p: p.stat().st_mtime)

        events = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").strip().splitlines()
            if line.strip()
        ]
        event_types = [e.get("event") for e in events]
        completed_sequence = [
            e.get("step_id", e.get("instance_id"))
            for e in events
            if e.get("event") == "step_completed"
        ]

        self.assertEqual(event_types[0], "run_started", f"first event was not run_started: {event_types}")
        self.assertEqual(event_types[-1], "run_completed", f"run did not complete cleanly: {event_types}")
        self.assertEqual(_EXPECTED_STEP_SEQUENCE, completed_sequence)


if __name__ == "__main__":
    unittest.main()
