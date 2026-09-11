"""Runs aggregate SRP workflow execution through Codex and Claude."""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from aggregate_srp_validation_e2e_live_base import (  # noqa: E402
    AggregateSRPValidationE2ELiveBase,
)
from claude_test_base import ClaudeTestBase  # noqa: E402
from codex_test_base import CodexTestBase  # noqa: E402


"""
solid-name: TestCodexAggregateSRPValidationLive
solid-category: integration-test
solid-spec: [SPEC-045]
solid-description: Verifies aggregate canonical SRP execution through the locked Codex profile.
"""
class TestCodexAggregateSRPValidationLive(
    CodexTestBase,
    AggregateSRPValidationE2ELiveBase,
):
    __test__ = True


"""
solid-name: TestClaudeAggregateSRPValidationLive
solid-category: integration-test
solid-spec: [SPEC-045]
solid-description: Verifies aggregate canonical SRP execution through the locked Claude profile.
"""
class TestClaudeAggregateSRPValidationLive(
    ClaudeTestBase,
    AggregateSRPValidationE2ELiveBase,
):
    __test__ = True
