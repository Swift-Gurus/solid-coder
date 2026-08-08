"""
solid-name: test_flow_e2e_live
solid-category: integration-test
solid-spec: [SPEC-031, SPEC-027]
solid-description: Applies the shared live flow-engine transition contract to Codex and Claude model-profile test bases.

Run one backend explicitly:
    python3 -m pytest tests/harness/flow_engine/test_flow_e2e_live.py::TestCodexFlowEngineE2ELive -v
    python3 -m pytest tests/harness/flow_engine/test_flow_e2e_live.py::TestClaudeFlowEngineE2ELive -v
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from claude_test_base import ClaudeTestBase  # noqa: E402
from codex_test_base import CodexTestBase  # noqa: E402
from flow_engine_e2e_live_base import FlowEngineE2ELiveBase  # noqa: E402


class TestCodexFlowEngineE2ELive(CodexTestBase, FlowEngineE2ELiveBase):

    __test__ = True


class TestClaudeFlowEngineE2ELive(ClaudeTestBase, FlowEngineE2ELiveBase):

    __test__ = True
