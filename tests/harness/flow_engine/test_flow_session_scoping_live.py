"""
solid-name: test_flow_session_scoping_live
solid-category: integration-test
solid-spec: [SPEC-031]
solid-description: Applies the shared child-session pointer contract to Codex and Claude model-profile test bases.

Run one backend explicitly:
    python3 -m pytest tests/harness/flow_engine/test_flow_session_scoping_live.py::TestCodexFlowSessionScopingLive -v
    python3 -m pytest tests/harness/flow_engine/test_flow_session_scoping_live.py::TestClaudeFlowSessionScopingLive -v
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from claude_test_base import ClaudeTestBase  # noqa: E402
from codex_test_base import CodexTestBase  # noqa: E402
from flow_session_scoping_e2e_live_base import (  # noqa: E402
    FlowSessionScopingE2ELiveBase,
)


class TestCodexFlowSessionScopingLive(
    CodexTestBase,
    FlowSessionScopingE2ELiveBase,
):

    __test__ = True


class TestClaudeFlowSessionScopingLive(
    ClaudeTestBase,
    FlowSessionScopingE2ELiveBase,
):

    __test__ = True
