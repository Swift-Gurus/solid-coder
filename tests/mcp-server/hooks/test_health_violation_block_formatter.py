"""Tests workflow health-violation reporting."""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path


ensure_on_path(
    Path(__file__).resolve().parents[3] / "mcp-server",
    Path(__file__).resolve().parent,
)

from health_violation import HealthViolation  # noqa: E402
from health_violation_block_formatter import (  # noqa: E402
    HealthViolationBlockFormatter,
)


"""
solid-name: TestHealthViolationBlockFormatter
solid-category: unit-test
solid-spec: [SPEC-036]
solid-description: Proves typed gate violations render their rule identity, reasoning, evidence, and fix guidance.
"""
class TestHealthViolationBlockFormatter(unittest.TestCase):
    def test_formats_typed_violation_evidence(self) -> None:
        reason = HealthViolationBlockFormatter().format_block_reason([
            HealthViolation(
                principle="srp",
                metric_id="SRP-2",
                issue="Two cohesion groups were measured.",
                evidence="Feature.swift:4-19",
                fix="Extract one responsibility.",
            )
        ])

        self.assertIn("1 SEVERE violation(s)", reason)
        self.assertIn("srp / SRP-2", reason)
        self.assertIn("Two cohesion groups were measured.", reason)
        self.assertIn("Feature.swift:4-19", reason)
        self.assertIn("Extract one responsibility.", reason)


if __name__ == "__main__":
    unittest.main()
