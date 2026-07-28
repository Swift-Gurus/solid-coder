"""
solid-name: test_flow_transition_gate_e2e_live
solid-category: integration-test
solid-description: Proves the flow_transition_gate Stop hook blocks a real Claude Code session
from ending its turn after submitting one of two steps and deliberately trying to stop early.

Not part of the fast unit-test sweep — spawns a real LLM session. Run explicitly:
    python3 tests/harness/flow_engine/test_flow_transition_gate_e2e_live.py

Uses --plugin-dir (not the globally installed plugin) so this dev repo's flow_transition_gate.py
is what actually loads — the installed plugin cache is a separate, independently-versioned
snapshot that does not see uncommitted work in this working tree.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

_MCP_SERVER = Path(__file__).resolve().parents[3] / "mcp-server"
_MCP_HEALTH_CONFIG = _MCP_SERVER / "health" / "config"
_TEST_DIR = Path(__file__).resolve().parent
for _d in (_MCP_SERVER, _MCP_HEALTH_CONFIG, _TEST_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hook_utils import solid_coder_project_dir  # noqa: E402
from mcp_config_builder import build_mcp_config  # noqa: E402
from test_flow_e2e_live import _run_claude_non_bare, _spawned_by_header  # noqa: E402

_PROJECT_ROOT = _MCP_SERVER.parent
# --plugin-dir registers the MCP server under a plugin-prefixed name
# (mcp__solid-coder-pipeline__*), distinct from the mcp__pipeline__* name used when the
# same server is passed via --mcp-config without --plugin-dir (see test_flow_e2e_live.py).
# Both are listed since either naming could resolve depending on plugin-discovery order.
_ALLOWED_TOOLS = (
    "mcp__pipeline__flow_start,mcp__pipeline__flow_next,"
    "mcp__solid-coder-pipeline__flow_start,mcp__solid-coder-pipeline__flow_next"
)

_TWO_STEP_FLOW_YAML = textwrap.dedent("""\
    name: transition_gate_e2e
    max_turns: 10
    steps:
      - id: step_one
        prompt: Reply with the single word "one".
      - id: step_two
        prompt: Reply with the single word "two".
        depends_on: [step_one]
""")


def _summarize_transcript(raw_stdout: str) -> str:
    """Best-effort readable dump of the session's --output-format json result, for failure diagnosis."""
    try:
        return "session result:\n" + json.dumps(json.loads(raw_stdout), indent=2)
    except (json.JSONDecodeError, ValueError):
        return f"raw stdout (not valid JSON):\n{raw_stdout}"


def _build_prompt(flow_file: Path, parent_session_id: str) -> str:
    return (
        f'{_spawned_by_header(parent_session_id)}'
        f'Call flow_start with flow="{flow_file}". Submit the output for the first step you are '
        "given via flow_next. Then, as a deliberate test of stop-time enforcement, try to end "
        "your turn immediately with a short closing message without submitting the second step. "
        "If a tool response or system message tells you the run isn't actually finished and to "
        "keep going, that's expected and correct — follow it and continue until the flow reports "
        "done, failed, or timed out."
    )


class TestFlowTransitionGateE2ELive(unittest.TestCase):

    TIMEOUT = 300

    def setUp(self):
        # Shares the real project's single main-run slot with test_flow_e2e_live.py. If this
        # test's own spawned session doesn't drive the run to a terminal state — the documented
        # early-stop non-determinism — runs/active.json is left pointing at a dead run, which
        # blocks the next flow_start (here or in the sibling test) with "Flow run already
        # active". Clear it before each run so a prior leak can't cascade.
        active_json = solid_coder_project_dir(_PROJECT_ROOT) / "runs" / "active.json"
        active_json.unlink(missing_ok=True)

    def test_stop_hook_blocks_early_termination_after_partial_submission(self):
        tmpdir = tempfile.mkdtemp()
        flow_file = Path(tmpdir) / "transition_gate_e2e.yaml"
        flow_file.write_text(_TWO_STEP_FLOW_YAML)

        runs_dir = solid_coder_project_dir(_PROJECT_ROOT) / "runs"
        before = set(runs_dir.glob("*/events.jsonl")) if runs_dir.exists() else set()

        parent_session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        result = _run_claude_non_bare(
            prompt=_build_prompt(flow_file, parent_session_id),
            allowed_tools=_ALLOWED_TOOLS,
            mcp_config=build_mcp_config(_PROJECT_ROOT),
            timeout=self.TIMEOUT,
            cwd=str(_PROJECT_ROOT),
            plugin_dir=str(_PROJECT_ROOT),
        )
        transcript = _summarize_transcript(result.stdout)

        after = set(runs_dir.glob("*/events.jsonl")) if runs_dir.exists() else set()
        new_logs = after - before
        self.assertTrue(new_logs, f"No new events.jsonl appeared after the session\n\n{transcript}")
        events_path = max(new_logs, key=lambda p: p.stat().st_mtime)

        events = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").strip().splitlines()
            if line.strip()
        ]
        event_types = [e.get("event") for e in events]

        # If the Stop hook did nothing, the agent would have honored its own instruction and
        # stopped after step_one — leaving the run in_progress with exactly one step_completed
        # and no run_completed. Reaching done proves the hook forced it to keep going.
        failure_detail = f"full event log: {event_types}\n\n{transcript}"
        self.assertEqual(event_types.count("step_completed"), 2, failure_detail)
        self.assertIn("run_completed", event_types, failure_detail)


if __name__ == "__main__":
    unittest.main()
