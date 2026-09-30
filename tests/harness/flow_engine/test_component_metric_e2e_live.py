"""Runs the shared component reducer live contract through both locked profiles."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from claude_test_base import ClaudeTestBase
from codex_test_base import CodexTestBase
from component_metric_e2e_live_base import ComponentMetricE2ELiveBase


"""
solid-name: TestCodexComponentMetricE2ELive
solid-category: integration-test
solid-spec: [SPEC-059]
solid-description: Applies the component metric live contract to the locked Codex model profile.
"""
class TestCodexComponentMetricE2ELive(CodexTestBase, ComponentMetricE2ELiveBase):
    __test__ = True


"""
solid-name: TestClaudeComponentMetricE2ELive
solid-category: integration-test
solid-spec: [SPEC-059]
solid-description: Applies the component metric live contract to the locked Claude model profile.
"""
class TestClaudeComponentMetricE2ELive(ClaudeTestBase, ComponentMetricE2ELiveBase):
    __test__ = True
