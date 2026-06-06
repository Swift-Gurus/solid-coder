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

# Cross-package: reuse mcp-server/tests base class and partial output builder
_MCP_DIR = _HERE.parents[2] / "mcp-server"
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))
from tests.helpers import SubmitFindingsTestBase, make_partial_output  # noqa: E402

from hc_checker import (  # noqa: E402
    LLMReviewer, LLMExecutor, FileBasedOutputHandler, FileOutputReader, HealthPromptBuilder,
)
from test_utils import make_test_executor  # noqa: E402


def _write_scored(output_dir: Path, label: str, doc: dict) -> None:
    """Write a pre-built scored doc to {output_dir}/{label}/review-output.json."""
    p = output_dir / label
    p.mkdir(parents=True, exist_ok=True)
    (p / "review-output.json").write_text(json.dumps(doc))


def _scored_srp(severity: str = "SEVERE") -> dict:
    """Extend make_partial_output with scoring/findings arrays for a single SRP unit."""
    doc = make_partial_output("srp", "Single Responsibility Principle", [
        {
            "file_path": "/tmp/Foo.swift",
            "units": [
                {
                    "unit_name": "Foo",
                    "unit_kind": "class",
                    "metrics": {},
                    "scoring": [{"metric_id": "SRP-1", "final_severity": severity}],
                    "findings": (
                        [{"metric_id": "SRP-1", "severity": severity,
                          "band_matched": "test", "metrics": {}}]
                        if severity in ("SEVERE", "MINOR") else []
                    ),
                }
            ],
        }
    ])
    doc["all_compliant"] = severity not in ("SEVERE", "MINOR")
    return doc


def _make_reviewer() -> LLMReviewer:
    executor, _ = make_test_executor()
    return LLMReviewer(
        executor=executor,
        output_handler=FileBasedOutputHandler(FileOutputReader()),
    )


class TestLLMReviewerBatch(SubmitFindingsTestBase):
    """Tests using SubmitFindingsTestBase for the temp directory (self.tmp)."""

    def test_reviewer_reads_violations_from_output_dir(self):
        _write_scored(Path(self.tmp.name), "SRP", _scored_srp())
        violations = _make_reviewer().review("prompt", "/tmp/Foo.swift",
                                              output_dir=self.tmp.name)
        self.assertIsNotNone(violations)
        self.assertGreater(len(violations), 0)

    def test_reviewer_violation_contains_principle_and_metric(self):
        _write_scored(Path(self.tmp.name), "SRP", _scored_srp())
        violations = _make_reviewer().review("prompt", "/tmp/Foo.swift",
                                              output_dir=self.tmp.name)
        v = violations[0]
        self.assertEqual(v["principle"], "Single Responsibility Principle")
        self.assertIn("metric_id", v)

    def test_reviewer_raises_when_no_files_found(self):
        with self.assertRaises(RuntimeError):
            _make_reviewer().review("prompt", "/tmp/Foo.swift", output_dir=self.tmp.name)

    def test_reviewer_aggregates_findings_from_multiple_principles(self):
        _write_scored(Path(self.tmp.name), "SRP", _scored_srp())
        dry_doc = make_partial_output("dry", "Don't Repeat Yourself", [
            {
                "file_path": "/tmp/Foo.swift",
                "units": [
                    {
                        "unit_name": "Foo",
                        "unit_kind": "class",
                        "metrics": {},
                        "scoring": [{"metric_id": "DRY-1", "final_severity": "SEVERE"}],
                        "findings": [{"metric_id": "DRY-1", "severity": "SEVERE",
                                      "band_matched": "test", "metrics": {}}],
                    }
                ],
            }
        ])
        dry_doc["all_compliant"] = False
        _write_scored(Path(self.tmp.name), "DRY", dry_doc)
        violations = _make_reviewer().review("prompt", "/tmp/Foo.swift",
                                              output_dir=self.tmp.name)
        principles = {v["principle"] for v in violations}
        self.assertIn("Single Responsibility Principle", principles)
        self.assertIn("Don't Repeat Yourself", principles)

    def test_reviewer_deletes_output_dir_after_reading(self):
        _write_scored(Path(self.tmp.name), "SRP", _scored_srp())
        _make_reviewer().review("prompt", "/tmp/Foo.swift", output_dir=self.tmp.name)
        self.assertFalse(Path(self.tmp.name).exists())

    def test_reviewer_deletes_output_dir_even_on_error(self):
        """Cleanup happens via finally even when RuntimeError is raised (no files found)."""
        with self.assertRaises(RuntimeError):
            _make_reviewer().review("prompt", "/tmp/Foo.swift", output_dir=self.tmp.name)
        self.assertFalse(Path(self.tmp.name).exists())

    def test_compliant_units_produce_no_violations(self):
        _write_scored(Path(self.tmp.name), "SRP", _scored_srp(severity="COMPLIANT"))
        violations = _make_reviewer().review("prompt", "/tmp/Foo.swift",
                                              output_dir=self.tmp.name)
        self.assertEqual(violations, [])


class TestHealthPromptBuilderOutputDir(unittest.TestCase):
    def test_build_accepts_output_dir_parameter(self):
        """build() accepts output_dir without error (infrastructure for submit_batch wiring)."""
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
