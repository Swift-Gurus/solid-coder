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
solid-description: Proves typed gate violations render correction guidance without exposing audit evidence or removing it from the finding.
"""
class TestHealthViolationBlockFormatter(unittest.TestCase):
    def test_formats_correction_guidance_without_audit_evidence(self) -> None:
        violation = HealthViolation(
            principle="srp",
            metric_id="SRP-2",
            issue="Two cohesion groups were measured.",
            evidence="Source method_variable_usage; matched indexes [1, 2]; excluded indexes [0].",
            fix="Extract one responsibility.",
        )

        reason = HealthViolationBlockFormatter().format_block_reason([violation])

        self.assertIn("1 SEVERE violation(s)", reason)
        self.assertIn("srp / SRP-2", reason)
        self.assertIn("Two cohesion groups were measured.", reason)
        self.assertNotIn("Evidence:", reason)
        self.assertNotIn(violation.evidence, reason)
        self.assertIn("Extract one responsibility.", reason)
        self.assertIn(violation.evidence, violation.model_dump_json())


if __name__ == "__main__":
    unittest.main()
