"""
solid-description: Verifies violation detection, context management, and invocation isolation in health checks.
solid-category: unit-test
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from _path_bootstrap import ensure_on_path

ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from hc_checker_factory import make_health_checker  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_SWIFT_CONTENT = "final class UserManager {\n" + "    func doThing() {}\n" * 12 + "}\n"

_SRP_VIOLATION = {
    "unit_name": "UserManager",
    "unit_kind": "class",
    "metrics": {"srp": {"verb_count": {"value": 12}}},
    "violations": [{"rule_id": "SRP-1", "severity": "SEVERE"}],
}

_SRP_CLEAN = {
    "unit_name": "UserManager",
    "unit_kind": "class",
    "metrics": {"srp": {"verb_count": {"value": 2}}},
    "violations": [],
}

_DETECTION_PRINCIPLES = [
    {
        "name": "srp",
        "content": "SRP detection rules",
        "principle_name": "SRP",
        "metrics_example": {},
    }
]

_MCP_CONFIG = '{"mcpServers": {}}'


# ---------------------------------------------------------------------------
# Subprocess router
# ---------------------------------------------------------------------------

def _make_subprocess_side_effect(
    solid_dir: Path,
    health_dirs: list,
    findings_sequence: list,
) -> object:
    """Return a subprocess.run side_effect routing gateway stubs and fake LLM calls.

    The fake LLM resolves its write target by reading active-health-check →
    hook-input.json, mirroring what _load_hook_context() does in the real MCP
    server. A regression in HealthCheckContextWriter will therefore break these
    tests rather than silently pass.
    """
    health_dir_iter = iter(health_dirs)
    llm_call_count = [0]

    def side_effect(cmd, **kwargs):
        joined = " ".join(str(a) for a in cmd)

        if "gateway.py" in joined:
            if "get_candidate_tags" in joined:
                return MagicMock(
                    returncode=0,
                    stdout=json.dumps({"candidate_tags": ["srp"]}),
                    stderr="",
                )
            if "load_detection_rules" in joined:
                return MagicMock(
                    returncode=0,
                    stdout=json.dumps({"principles": _DETECTION_PRINCIPLES}),
                    stderr="",
                )
            if "get_output_path" in joined:
                return MagicMock(
                    returncode=0,
                    stdout=json.dumps({"output_root": str(next(health_dir_iter))}),
                    stderr="",
                )

        findings = findings_sequence[llm_call_count[0]]
        llm_call_count[0] += 1

        pointer = solid_dir / "active-health-check"
        health_id = pointer.read_text(encoding="utf-8").strip()
        hook_input = json.loads(
            (solid_dir / health_id / "hook-input.json").read_text(encoding="utf-8")
        )
        out_dir = Path(hook_input["output_dir"])

        for principle, units in findings.items():
            d = out_dir / principle
            d.mkdir(parents=True, exist_ok=True)
            (d / "review-output.json").write_text(
                json.dumps({
                    "timestamp": "2026-01-01T00:00:00Z",
                    "files": [{"file_path": hook_input["file_path"], "units": units}],
                }),
                encoding="utf-8",
            )

        return MagicMock(
            returncode=0,
            stdout=json.dumps([{"type": "result", "result": "done"}]),
            stderr="",
        )

    return side_effect


# ---------------------------------------------------------------------------
# Base test infrastructure
# ---------------------------------------------------------------------------

class _E2EBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.solid_dir = Path(self.tmp.name) / "solid-coder-project"
        self.solid_dir.mkdir()

    def _health_dir(self, name: str) -> Path:
        return self.solid_dir / name

    def _run_checks(
        self,
        findings_sequence: list,
        health_dirs: list = None,
        file_path: str = "/src/Foo.swift",
        session_id: str = "test-session",
    ) -> list:
        if health_dirs is None:
            health_dirs = [self._health_dir(f"health-run-{i}") for i in range(len(findings_sequence))]

        side_effect = _make_subprocess_side_effect(self.solid_dir, health_dirs, findings_sequence)

        results = []
        with (
            patch("hc_runner_factory.llm_backend", return_value="claude"),
            patch("hook_utils.subprocess.run", side_effect=side_effect),
            patch(
                "health_check_context_writer.solid_coder_project_dir",
                return_value=self.solid_dir,
            ),
            patch("hc_checker_factory.debug_mode", return_value=True),
        ):
            checker = make_health_checker(mcp_config=_MCP_CONFIG)
            for _ in findings_sequence:
                results.append(checker.check(_SWIFT_CONTENT, file_path, "Swift", session_id))
        return results


# ---------------------------------------------------------------------------
# Violation flow tests
# ---------------------------------------------------------------------------

class TestViolationFlow(_E2EBase):
    """Violations written by the fake LLM flow through the full pipeline."""

    def test_severe_violations_returned(self):
        violations = self._run_checks([{"srp": [_SRP_VIOLATION]}])[0]
        self.assertIsInstance(violations, list)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["principle"], "SRP")
        self.assertEqual(violations[0]["metric_id"], "SRP-1")

    def test_clean_file_returns_empty_list(self):
        result = self._run_checks([{"srp": [_SRP_CLEAN]}])[0]
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# Context writer tests
# ---------------------------------------------------------------------------

class TestContextWriter(_E2EBase):
    """HealthCheckContextWriter writes hook-input.json and clears the pointer after check."""

    def test_hook_input_json_contains_file_path_language_and_output_dir(self):
        h = self._health_dir("health-run-0")
        file_path = "/src/MyViewModel.swift"
        self._run_checks([{"srp": [_SRP_CLEAN]}], health_dirs=[h], file_path=file_path)
        hook_input = json.loads((h / "hook-input.json").read_text(encoding="utf-8"))
        self.assertEqual(hook_input["file_path"], file_path)
        self.assertEqual(hook_input["language"], "Swift")
        self.assertEqual(hook_input["output_dir"], str(h))

    def test_pointer_cleared_after_check_completes(self):
        h = self._health_dir("health-run-0")
        self._run_checks([{"srp": [_SRP_CLEAN]}], health_dirs=[h])
        pointer = self.solid_dir / "active-health-check"
        self.assertFalse(pointer.exists(), "active-health-check must be deleted after check() returns")

    def test_pointer_cleared_after_each_of_two_runs(self):
        h1 = self._health_dir("health-run-0")
        h2 = self._health_dir("health-run-1")
        self._run_checks(
            [{"srp": [_SRP_CLEAN]}, {"srp": [_SRP_CLEAN]}],
            health_dirs=[h1, h2],
        )
        pointer = self.solid_dir / "active-health-check"
        self.assertFalse(pointer.exists(), "active-health-check must be absent after last check() returns")


# ---------------------------------------------------------------------------
# Isolation tests
# ---------------------------------------------------------------------------

class TestInvocationIsolation(_E2EBase):
    """Each check() invocation uses its own health dir; stale files cannot bleed."""

    def test_each_invocation_resolves_a_unique_health_dir(self):
        h1 = self._health_dir("health-run-0")
        h2 = self._health_dir("health-run-1")
        self._run_checks(
            [{"srp": [_SRP_CLEAN]}, {"srp": [_SRP_CLEAN]}],
            health_dirs=[h1, h2],
        )
        self.assertTrue(h1.exists(), "First health dir not created")
        self.assertTrue(h2.exists(), "Second health dir not created")
        self.assertNotEqual(h1, h2)

    def test_stale_violations_from_run1_do_not_affect_run2(self):
        """
        Run1 produces SEVERE violations; run2 is clean.
        With cleanup disabled (debug=True), run1's files persist on disk —
        but run2 reads only from its own dir, so it must still return [].
        """
        h1 = self._health_dir("health-run-0")
        h2 = self._health_dir("health-run-1")

        results = self._run_checks(
            [{"srp": [_SRP_VIOLATION]}, {"srp": [_SRP_CLEAN]}],
            health_dirs=[h1, h2],
        )

        self.assertEqual(len(results[0]), 1, "Run1 should report 1 violation")
        self.assertEqual(len(results[1]), 0, "Run2 must not inherit run1's violations")

        stale_files = list(h1.glob("*/review-output.json"))
        self.assertTrue(stale_files, "Run1 findings should still be on disk (debug=True)")

        for f in h2.glob("*/review-output.json"):
            doc = json.loads(f.read_text(encoding="utf-8"))
            for file_obj in doc.get("files", []):
                for unit in file_obj.get("units", []):
                    severe = [v for v in unit.get("violations", []) if v.get("severity") == "SEVERE"]
                    self.assertEqual(
                        severe, [],
                        f"Run2 dir contains stale SEVERE violations in {f}",
                    )


if __name__ == "__main__":
    unittest.main()
