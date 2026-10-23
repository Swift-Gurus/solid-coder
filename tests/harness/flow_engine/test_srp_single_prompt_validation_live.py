"""
solid-name: test_srp_single_prompt_validation_live
solid-category: integration-test
solid-spec: [SPEC-036]
solid-description: Runs the one-call SRP prompt experiment through reusable Codex and Claude live profiles.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIRECTORY = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIRECTORY))

from claude_test_base import ClaudeTestBase
from codex_test_base import CodexTestBase
from srp_single_prompt_validation_e2e_live_base import (
    SRPSinglePromptValidationE2ELiveBase,
)


class TestCodexSRPSinglePromptValidationLive(
    CodexTestBase,
    SRPSinglePromptValidationE2ELiveBase,
):
    __test__ = True


class TestClaudeSRPSinglePromptValidationLive(
    ClaudeTestBase,
    SRPSinglePromptValidationE2ELiveBase,
):
    __test__ = True
