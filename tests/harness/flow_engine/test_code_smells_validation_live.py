"""
solid-name: test_code_smells_validation_live
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-055]
solid-description: Applies the locked Code Smells workflow contract to Codex and Claude model profiles.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from claude_test_base import ClaudeTestBase  # noqa: E402
from code_smells_validation_e2e_live_base import (  # noqa: E402
    CodeSmellsValidationE2ELiveBase,
)
from codex_test_base import CodexTestBase  # noqa: E402
from code_smells_boundary_e2e_live_base import CodeSmellsBoundaryE2ELiveBase


class TestCodexCodeSmellsValidationLive(
    CodexTestBase,
    CodeSmellsValidationE2ELiveBase,
):
    __test__ = True


class TestClaudeCodeSmellsValidationLive(
    ClaudeTestBase,
    CodeSmellsValidationE2ELiveBase,
):
    __test__ = True


class TestCodexCodeSmellsBoundaryLive(CodexTestBase, CodeSmellsBoundaryE2ELiveBase):
    __test__ = True


class TestClaudeCodeSmellsBoundaryLive(ClaudeTestBase, CodeSmellsBoundaryE2ELiveBase):
    __test__ = True
