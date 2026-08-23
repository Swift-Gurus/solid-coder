"""Runs the locked composite review smoke scenario through Codex Terra."""

import sys
from pathlib import Path

_HARNESS = Path(__file__).resolve().parents[1]
if str(_HARNESS) not in sys.path:
    sys.path.insert(0, str(_HARNESS))

from codex_test_base import CodexTestBase  # noqa: E402
from solid_review_comparison_e2e_live_base import (  # noqa: E402
    SolidReviewComparisonE2ELiveBase,
)


"""
solid-name: TestCodexSolidReviewComparisonLive
solid-category: integration-test
solid-spec: [SPEC-036, SPEC-041]
solid-description: Proves the composite workflow-review comparison path completes under the pinned Codex Terra profile before repeated measurement.
"""
class TestCodexSolidReviewComparisonLive(
    CodexTestBase,
    SolidReviewComparisonE2ELiveBase,
):
    __test__ = True
