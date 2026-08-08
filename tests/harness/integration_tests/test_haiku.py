"""
solid-name: TestHaikuPrincipleReview
solid-category: integration-test
solid-description: Integration tests for all principles using claude-haiku-4-5.
Runs apply and health flows against all fixture-backed principles.
Expectation mismatches are acceptable at this stage — only infrastructure
failures cause test failure.

Run:
    python3 -m pytest tests/harness/integration_tests/test_haiku.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from claude_test_base import ClaudeTestBase  # noqa: E402
from integration_tests.base import IntegrationTestBase  # noqa: E402


class TestHaikuPrincipleReview(ClaudeTestBase, IntegrationTestBase):
    """Principle review integration tests using claude-haiku-4-5.

    Haiku is the fastest and cheapest Claude model — use it for rapid
    sanity checks of the harness and detection pipeline.
    Timeout is lower than opus because haiku responses are faster.
    """

    __test__ = True
    MODEL_PROFILE = "haiku"
    TIMEOUT = 180
