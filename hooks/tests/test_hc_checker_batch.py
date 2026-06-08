"""
solid-description: Validates batch health check output collection, cross-principle aggregation, and cleanup behavior.
solid-category: unit-test
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from _path_bootstrap import ensure_on_path

_HERE = Path(__file__).resolve()
ensure_on_path(_HERE.parents[1], _HERE.parent)

from hc_checker import (  # noqa: E402
    LLMReviewer, LLMExecutor, FileBasedOutputHandler, FileOutputReader, HealthPromptBuilder,
)
from test_utils import make_test_executor  # noqa: E402


def _write_review_output(output_dir: Path, label: str, violations: list) -> None:
    """Write a review-output.json in the new unified format."""
    p = output_dir / label
    p.mkdir(parents=True, exist_ok=True)
    (p / "review-output.json").write_text(json.dumps({
        "timestamp": "2026-01-01T00:00:00Z",
        "files": [{"file_path": "/tmp/Foo.swift", "units": [{
            "unit_name": "Foo",
            "unit_kind": "class",
            "metrics": {},
            "violations": violations,
        }]}],
    }))


def _violation(rule_id: str, severity: str = "SEVERE") -> dict:
    return {"rule_id": rule_id, "severity": severity}


def _make_reviewer() -> LLMReviewer:
    executor, _ = make_test_executor()
    return LLMReviewer(
        executor=executor,
        output_handler=FileBasedOutputHandler(FileOutputReader()),
    )


class TestLLMReviewerBatch(unittest.TestCase):
    """Tests using a temp directory via setUp."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    @property
    def tmp_path(self):
        return Path(self.tmp.name)

    def test_reviewer_reads_violations_from_output_dir(self):
        _write_review_output(self.tmp_path, "SRP", [_violation("SRP-1")])
        violations = _make_reviewer().review("prompt", "/tmp/Foo.swift",
                                              output_dir=self.tmp.name)
        self.assertIsNotNone(violations)
        self.assertGreater(len(violations), 0)

    def test_reviewer_violation_contains_principle_and_metric(self):
        _write_review_output(self.tmp_path, "SRP", [_violation("SRP-1")])
        violations = _make_reviewer().review("prompt", "/tmp/Foo.swift",
                                              output_dir=self.tmp.name)
        v = violations[0]
        self.assertEqual(v["principle"], "SRP")
        self.assertIn("metric_id", v)

    def test_reviewer_raises_when_no_files_found(self):
        with self.assertRaises(RuntimeError):
            _make_reviewer().review("prompt", "/tmp/Foo.swift", output_dir=self.tmp.name)

    def test_reviewer_aggregates_violations_from_multiple_principles(self):
        _write_review_output(self.tmp_path, "SRP", [_violation("SRP-1")])
        _write_review_output(self.tmp_path, "DRY", [_violation("DRY-3")])
        violations = _make_reviewer().review("prompt", "/tmp/Foo.swift",
                                              output_dir=self.tmp.name)
        principles = {v["principle"] for v in violations}
        self.assertIn("SRP", principles)
        self.assertIn("DRY", principles)

    def test_reviewer_deletes_output_dir_after_reading(self):
        _write_review_output(self.tmp_path, "SRP", [_violation("SRP-1")])
        _make_reviewer().review("prompt", "/tmp/Foo.swift", output_dir=self.tmp.name)
        self.assertFalse(Path(self.tmp.name).exists())

    def test_reviewer_deletes_output_dir_even_on_error(self):
        with self.assertRaises(RuntimeError):
            _make_reviewer().review("prompt", "/tmp/Foo.swift", output_dir=self.tmp.name)
        self.assertFalse(Path(self.tmp.name).exists())

    def test_compliant_units_produce_no_violations(self):
        _write_review_output(self.tmp_path, "SRP", [])
        violations = _make_reviewer().review("prompt", "/tmp/Foo.swift",
                                              output_dir=self.tmp.name)
        self.assertEqual(violations, [])


class TestHealthPromptBuilderOutputDir(unittest.TestCase):
    def test_build_accepts_output_dir_parameter(self):
        builder = HealthPromptBuilder()
        prompt = builder.build(
            principles=[{"content": "rule text"}],
            content="class Foo {}",
            path="/tmp/Foo.swift",
            parent_session_id="sess-123",
            output_dir="/home/user/.solid-coder/gate/sess-123",
        )
        self.assertIsInstance(prompt, str)
        self.assertIn("rule text", prompt)


if __name__ == "__main__":
    unittest.main()
