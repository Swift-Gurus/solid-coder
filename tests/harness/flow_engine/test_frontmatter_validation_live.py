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


class TestCodexInvalidFrontmatterValidationLive(TestCodexFrontmatterValidationLive):
    FIXTURE = TestCodexFrontmatterValidationLive.FIXTURE.with_name("fixture-2.swift")
    ARTIFACT_SCENARIO = "frontmatter-invalid"
    EXPECTED_VALUES = [0, 1, 1, 1, 1]
    EXPECTED_METRIC_SEVERITIES = ["COMPLIANT", "SEVERE", "SEVERE", "SEVERE", "SEVERE"]
    EXPECTED_ANALYSIS_STEP_IDS = ["analyze_source", "prepare_frontmatter", "classify_descriptions", "bind_descriptions"]


class TestClaudeInvalidFrontmatterValidationLive(TestClaudeFrontmatterValidationLive):
    FIXTURE = TestCodexInvalidFrontmatterValidationLive.FIXTURE
    ARTIFACT_SCENARIO = TestCodexInvalidFrontmatterValidationLive.ARTIFACT_SCENARIO
    EXPECTED_VALUES = TestCodexInvalidFrontmatterValidationLive.EXPECTED_VALUES
    EXPECTED_METRIC_SEVERITIES = TestCodexInvalidFrontmatterValidationLive.EXPECTED_METRIC_SEVERITIES
    EXPECTED_ANALYSIS_STEP_IDS = TestCodexInvalidFrontmatterValidationLive.EXPECTED_ANALYSIS_STEP_IDS


class TestCodexCompliantFrontmatterValidationLive(TestCodexFrontmatterValidationLive):
    FIXTURE = TestCodexFrontmatterValidationLive.FIXTURE.with_name("fixture-3.swift")
    ARTIFACT_SCENARIO = "frontmatter-compliant"
    EXPECTED_VALUES = [0, 0, 0, 0, 0]
    EXPECTED_METRIC_SEVERITIES = ["COMPLIANT"] * 5
    EXPECTED_FINAL_SEVERITY = "COMPLIANT"
    EXPECTED_ANALYSIS_STEP_IDS = TestCodexInvalidFrontmatterValidationLive.EXPECTED_ANALYSIS_STEP_IDS


class TestClaudeCompliantFrontmatterValidationLive(TestClaudeFrontmatterValidationLive):
    FIXTURE = TestCodexCompliantFrontmatterValidationLive.FIXTURE
    ARTIFACT_SCENARIO = TestCodexCompliantFrontmatterValidationLive.ARTIFACT_SCENARIO
    EXPECTED_VALUES = TestCodexCompliantFrontmatterValidationLive.EXPECTED_VALUES
    EXPECTED_METRIC_SEVERITIES = TestCodexCompliantFrontmatterValidationLive.EXPECTED_METRIC_SEVERITIES
    EXPECTED_FINAL_SEVERITY = "COMPLIANT"
    EXPECTED_ANALYSIS_STEP_IDS = TestCodexCompliantFrontmatterValidationLive.EXPECTED_ANALYSIS_STEP_IDS
