"""Verifies typed gate findings at the unchanged legacy extractor boundary."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import TypeAdapter, ValidationError

_ROOT = Path(__file__).resolve().parents[3]
for _part in ("", "health", "output", "utils"):
    sys.path.insert(0, str(_ROOT / "mcp-server" / _part))

from health_violation import HealthViolation
from legacy_health_violation_payload import LegacyHealthViolationPayload
from typed_legacy_violation_extractor import TypedLegacyViolationExtractor


"""
solid-name: TestTypedLegacyViolationExtractor
solid-category: unit-test
solid-spec: [SPEC-050]
solid-description: Verifies legacy findings become typed gate violations without changing legacy extraction.
"""
class TestTypedLegacyViolationExtractor:
    def _extractor(self, legacy):
        return TypedLegacyViolationExtractor(
            legacy=legacy,
            adapter=TypeAdapter(list[LegacyHealthViolationPayload]),
        )

    def test_converts_legacy_finding_with_explicit_missing_evidence(self):
        legacy = MagicMock()
        legacy.extract.return_value = [{
            "principle": "CS",
            "metric_id": "CS-2",
            "file_path": "/project/example.py",
            "unit_name": "example.py",
            "issue": "CS-2 is severe",
            "fix": "Split unrelated types.",
        }]

        violations = self._extractor(legacy).extract("/review-output")

        assert violations == [HealthViolation(
            principle="CS",
            metric_id="CS-2",
            issue="CS-2 is severe",
            evidence="Legacy output did not preserve evidence for CS-2.",
            fix="Split unrelated types.",
        )]
        legacy.extract.assert_called_once_with("/review-output")

    def test_rejects_malformed_legacy_finding(self):
        legacy = MagicMock()
        legacy.extract.return_value = [{
            "principle": "CS",
            "metric_id": "",
            "issue": "CS-2 is severe",
            "fix": "Split unrelated types.",
        }]

        with pytest.raises(ValidationError):
            self._extractor(legacy).extract("/review-output")
