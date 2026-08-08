"""
solid-name: test_srp_validation_live
solid-category: integration-test
solid-spec: [SPEC-034]
solid-description: Applies the exact SRP workflow contract to Codex and Claude model-profile test bases.

Run one backend explicitly:
    python3 -m pytest tests/harness/flow_engine/test_srp_validation_live.py::TestCodexSRPValidationLive -v -s
    python3 -m pytest tests/harness/flow_engine/test_srp_validation_live.py::TestClaudeSRPValidationLive -v -s
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from claude_test_base import ClaudeTestBase  # noqa: E402
from codex_test_base import CodexTestBase  # noqa: E402
from srp_validation_e2e_live_base import SRPValidationE2ELiveBase  # noqa: E402


class TestCodexSRPValidationLive(CodexTestBase, SRPValidationE2ELiveBase):

    __test__ = True


class TestClaudeSRPValidationLive(ClaudeTestBase, SRPValidationE2ELiveBase):

    __test__ = True
