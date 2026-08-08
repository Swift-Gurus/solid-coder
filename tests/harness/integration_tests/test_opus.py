"""
solid-name: TestOpusPrincipleReview
solid-category: integration-test
solid-description: Integration tests for all principles using claude-opus-4-5.
Runs apply and health flows against all fixture-backed principles.
Expectation mismatches are acceptable at this stage — only infrastructure
failures cause test failure.

Run:
    python3 -m pytest tests/harness/integration_tests/test_opus.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from claude_test_base import ClaudeTestBase  # noqa: E402
from integration_tests.base import IntegrationTestBase  # noqa: E402


class TestOpusPrincipleReview(ClaudeTestBase, IntegrationTestBase):
    """Principle review integration tests using claude-opus-4-5.

    Opus is the highest-capability Claude model — use it to establish
    best-case detection quality against the fixture expectations.
    Higher timeout than haiku because opus responses are slower.
    """

    __test__ = True
    MODEL_PROFILE = "opus"
    TIMEOUT = 300
