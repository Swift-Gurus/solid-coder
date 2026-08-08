"""
solid-name: TestSonnetPrincipleReview
solid-category: integration-test
solid-description: Integration tests for all principles using claude-sonnet-4-6.
Runs apply and health flows against all fixture-backed principles.
Expectation mismatches are acceptable at this stage — only infrastructure
failures cause test failure.

Run:
    python3 -m pytest tests/harness/integration_tests/test_sonnet.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from claude_test_base import ClaudeTestBase  # noqa: E402
from integration_tests.base import IntegrationTestBase  # noqa: E402


class TestSonnetPrincipleReview(ClaudeTestBase, IntegrationTestBase):
    """Principle review integration tests using claude-sonnet-4-6.

    Sonnet balances capability and speed — use it as a realistic
    production-quality baseline between haiku and opus.
    """

    __test__ = True
    MODEL_PROFILE = "sonnet"
    TIMEOUT = 300
