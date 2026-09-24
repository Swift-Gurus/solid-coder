"""
solid-name: test_frontmatter_validation_live
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-055]
solid-description: Applies the locked Frontmatter workflow contract to Codex and Claude model profiles.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from claude_test_base import ClaudeTestBase  # noqa: E402
from codex_test_base import CodexTestBase  # noqa: E402
from frontmatter_validation_e2e_live_base import (  # noqa: E402
    FrontmatterValidationE2ELiveBase,
)


class TestCodexFrontmatterValidationLive(
    CodexTestBase,
    FrontmatterValidationE2ELiveBase,
):
    __test__ = True


class TestClaudeFrontmatterValidationLive(
    ClaudeTestBase,
    FrontmatterValidationE2ELiveBase,
):
    __test__ = True
