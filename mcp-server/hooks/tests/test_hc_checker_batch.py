"""
solid-description: Validates batch health check output collection, cross-principle aggregation, cleanup, and invocation isolation.
solid-category: unit-test
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from _path_bootstrap import ensure_on_path

_HERE = Path(__file__).resolve()
ensure_on_path(_HERE.parents[1], _HERE.parent)

from hc_checker import (  # noqa: E402
    LLMReviewer, LLMExecutor, FileBasedOutputHandler, FileOutputReader,
    HealthPromptBuilder, LLMHealthChecker,
)
from violation_extractor import ViolationExtractor  # noqa: E402
from test_utils import make_test_executor  # noqa: E402


class TestLLMReviewerBatch(unittest.TestCase):
    """Tests for batch review output collection, aggregation, cleanup, and invocation isolation."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    @property
    def tmp_path(self):
        return Path(self.tmp.name)

    def _write_review_output(self, output_dir: Path, label: str, violations: list) -> None:
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

    def _violation(self, rule_id: str, severity: str = "SEVERE") -> dict:
        return {"rule_id": rule_id, "severity": severity}

    def _make_reviewer(self) -> LLMReviewer:
        executor, _ = make_test_executor()
        return LLMReviewer(
            executor=executor,
            output_handler=FileBasedOutputHandler(FileOutputReader(extractor=ViolationExtractor())),
        )

    def _make_checker(self, resolver, reviewer=None):
        loader = MagicMock()
        loader.load.return_value = [{"name": "srp", "content": "rules"}]
        if reviewer is None:
            reviewer = MagicMock()
            reviewer.review.return_value = []
        return LLMHealthChecker(
            loader=loader,
            builder=HealthPromptBuilder(),
            reviewer=reviewer,
            path_resolver=resolver,
        )

    # ── Reviewer batch tests ───────────────────────────────────────────────────

    def test_reviewer_reads_violations_from_output_dir(self):
        self._write_review_output(self.tmp_path, "SRP", [self._violation("SRP-1")])
        violations = self._make_reviewer().review("prompt", "/tmp/Foo.swift",
                                                   output_dir=self.tmp.name)
        self.assertIsNotNone(violations)
        self.assertGreater(len(violations), 0)

    def test_reviewer_violation_contains_principle_and_metric(self):
        self._write_review_output(self.tmp_path, "SRP", [self._violation("SRP-1")])
        violations = self._make_reviewer().review("prompt", "/tmp/Foo.swift",
                                                   output_dir=self.tmp.name)
        v = violations[0]
        self.assertEqual(v["principle"], "SRP")
        self.assertIn("metric_id", v)

    def test_reviewer_raises_when_no_files_found(self):
        with self.assertRaises(RuntimeError):
            self._make_reviewer().review("prompt", "/tmp/Foo.swift", output_dir=self.tmp.name)

    def test_reviewer_aggregates_violations_from_multiple_principles(self):
        self._write_review_output(self.tmp_path, "SRP", [self._violation("SRP-1")])
        self._write_review_output(self.tmp_path, "DRY", [self._violation("DRY-3")])
        violations = self._make_reviewer().review("prompt", "/tmp/Foo.swift",
                                                   output_dir=self.tmp.name)
        principles = {v["principle"] for v in violations}
        self.assertIn("SRP", principles)
        self.assertIn("DRY", principles)

    def test_reviewer_deletes_output_dir_after_reading(self):
        self._write_review_output(self.tmp_path, "SRP", [self._violation("SRP-1")])
        self._make_reviewer().review("prompt", "/tmp/Foo.swift", output_dir=self.tmp.name)
        self.assertFalse(Path(self.tmp.name).exists())

    def test_reviewer_deletes_output_dir_even_on_error(self):
        with self.assertRaises(RuntimeError):
            self._make_reviewer().review("prompt", "/tmp/Foo.swift", output_dir=self.tmp.name)
        self.assertFalse(Path(self.tmp.name).exists())

    def test_compliant_units_produce_no_violations(self):
        self._write_review_output(self.tmp_path, "SRP", [])
        violations = self._make_reviewer().review("prompt", "/tmp/Foo.swift",
                                                   output_dir=self.tmp.name)
        self.assertEqual(violations, [])

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

    # ── Invocation isolation tests ─────────────────────────────────────────────

    def test_each_invocation_receives_a_different_output_dir(self):
        """Resolver is called once per check() — two calls must yield two distinct dirs."""
        dirs_resolved = []
        dirs_reviewed = []

        class CapturingResolver:
            def resolve(self, session_id):
                path = f"/tmp/gate/health-{len(dirs_resolved):04d}"
                dirs_resolved.append(path)
                return path

        class CapturingReviewer:
            def review(self, prompt, path, output_dir=None):
                dirs_reviewed.append(output_dir)
                return []

        checker = self._make_checker(CapturingResolver(), CapturingReviewer())
        checker.check("code", "/src/Foo.swift", "Swift", "session-abc")
        checker.check("code", "/src/Bar.swift", "Swift", "session-abc")

        self.assertEqual(len(dirs_resolved), 2)
        self.assertNotEqual(dirs_resolved[0], dirs_resolved[1])
        self.assertEqual(dirs_reviewed[0], dirs_resolved[0])
        self.assertEqual(dirs_reviewed[1], dirs_resolved[1])

    def test_stale_files_in_run1_dir_do_not_affect_run2(self):
        """Run 1 violations on disk must not appear in run 2's isolated directory."""
        base = tempfile.mkdtemp()
        dir1 = Path(base) / "run1"
        dir2 = Path(base) / "run2"
        dir2.mkdir(parents=True)

        call_count = [0]

        class SequentialResolver:
            def resolve(self, session_id):
                call_count[0] += 1
                return str(dir1) if call_count[0] == 1 else str(dir2)

        # Plant a stale violation in dir1
        dir1.mkdir(parents=True)
        self._write_review_output(dir1, "SRP", [self._violation("SRP-1")])

        run = [0]

        class RunTrackingReviewer:
            def review(self, prompt, path, output_dir=None):
                run[0] += 1
                if run[0] == 2:
                    raise RuntimeError("No output in run 2 dir")
                return []

        checker = self._make_checker(SequentialResolver(), RunTrackingReviewer())
        checker.check("code", "/src/Foo.swift", "Swift", "sess")
        with self.assertRaises(RuntimeError):
            checker.check("code", "/src/Bar.swift", "Swift", "sess")

        # dir2 must be empty — no bleed from dir1
        self.assertEqual(list(dir2.glob("*/review-output.json")), [])


if __name__ == "__main__":
    unittest.main()
