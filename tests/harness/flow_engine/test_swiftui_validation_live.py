"""
solid-name: test_swiftui_validation_live
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-055, SPEC-057]
solid-description: Applies the locked SwiftUI workflow contract to Codex and Claude model profiles.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from claude_test_base import ClaudeTestBase
from codex_test_base import CodexTestBase
from swiftui_validation_e2e_live_base import (
    SwiftUIValidationE2ELiveBase,
)


class TestCodexSwiftUIValidationLive(
    CodexTestBase,
    SwiftUIValidationE2ELiveBase,
):
    __test__ = True


class TestClaudeSwiftUIValidationLive(
    ClaudeTestBase,
    SwiftUIValidationE2ELiveBase,
):
    __test__ = True
