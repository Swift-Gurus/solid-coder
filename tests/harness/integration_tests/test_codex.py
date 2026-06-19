"""
solid-name: TestCodexPrincipleReview
solid-category: integration-test
solid-description: Integration tests for all principles using the Codex backend.
Runs apply and health flows against all fixture-backed principles.
Expectation mismatches are acceptable at this stage — only infrastructure
failures cause test failure.

Run:
    python3 -m pytest tests/harness/integration_tests/test_codex.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integration_tests.base import IntegrationTestBase  # noqa: E402


class TestCodexPrincipleReview(IntegrationTestBase):
    """Principle review integration tests using the Codex backend.

    Uses the codex.toml model profile which routes to the Codex LLM backend.
    Timeout matches the profile's configured limit.
    """

    __test__ = True
    MODEL_PROFILE = "codex"
    TIMEOUT = 300
