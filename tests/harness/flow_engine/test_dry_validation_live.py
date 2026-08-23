"""
solid-name: test_dry_validation_live
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-040]
solid-description: Applies the exact unit-scoped DRY workflow contract to Codex and Claude model-profile test bases.

Run one backend explicitly:
    python3 -m pytest tests/harness/flow_engine/test_dry_validation_live.py::TestCodexDRYValidationLive -v -s
    python3 -m pytest tests/harness/flow_engine/test_dry_validation_live.py::TestClaudeDRYValidationLive -v -s
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from claude_test_base import ClaudeTestBase  # noqa: E402
from codex_test_base import CodexTestBase  # noqa: E402
from dry_validation_e2e_live_base import DRYValidationE2ELiveBase  # noqa: E402


class TestCodexDRYValidationLive(CodexTestBase, DRYValidationE2ELiveBase):

    __test__ = True


class TestClaudeDRYValidationLive(ClaudeTestBase, DRYValidationE2ELiveBase):

    __test__ = True
