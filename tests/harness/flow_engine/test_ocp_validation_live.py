"""
solid-name: test_ocp_validation_live
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Applies the exact OCP workflow contract to Codex and Claude model-profile test bases.

Run one backend explicitly:
    python3 -m pytest tests/harness/flow_engine/test_ocp_validation_live.py::TestCodexOCPValidationLive -v -s
    python3 -m pytest tests/harness/flow_engine/test_ocp_validation_live.py::TestClaudeOCPValidationLive -v -s
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from claude_test_base import ClaudeTestBase  # noqa: E402
from codex_test_base import CodexTestBase  # noqa: E402
from ocp_validation_e2e_live_base import OCPValidationE2ELiveBase  # noqa: E402


class TestCodexOCPValidationLive(CodexTestBase, OCPValidationE2ELiveBase):

    __test__ = True


class TestClaudeOCPValidationLive(ClaudeTestBase, OCPValidationE2ELiveBase):

    __test__ = True
