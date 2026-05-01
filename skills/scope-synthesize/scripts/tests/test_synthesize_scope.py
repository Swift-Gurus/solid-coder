#!/usr/bin/env python3
"""CLI contract tests for synthesize-scope.py."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "synthesize-scope.py"


def run(heuristic: dict, skeleton: dict, cohesion: dict) -> dict:
    """Write the three input JSONs and invoke the script. Return the parsed output."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "heuristic.json").write_text(json.dumps(heuristic), encoding="utf-8")
        (tmp_path / "skeleton.json").write_text(json.dumps(skeleton), encoding="utf-8")
        (tmp_path / "cohesion.json").write_text(json.dumps(cohesion), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"script failed: {result.stderr}")
        return json.loads((tmp_path / "scope-assessment.json").read_text(encoding="utf-8"))


def heuristic_input(loc=180):
    return {"spec_path": "/x", "ac_count": 15, "screens": 0, "predicted_loc": loc, "formula": "f", "severity": "COMPLIANT", "by_story": []}


def skeleton_input(skeleton_loc=110, projected=187):
    return {
        "spec_path": "/x", "language": "Swift", "skeleton_loc": skeleton_loc,
        "multiplier_used": 1.7, "projected_loc": projected, "severity": "COMPLIANT",
        "skeleton_files": [],
    }


def cohesion_input(group_count=1, severity="COMPLIANT", groups=None):
    return {"spec_path": "/x", "group_count": group_count, "severity": severity, "groups": groups or []}


class Verdicts(unittest.TestCase):
    def test_all_compliant_returns_compliant(self):
        out = run(heuristic_input(), skeleton_input(), cohesion_input())
        self.assertEqual(out["verdict"], "compliant")
        self.assertFalse(out["split_recommendation"]["should_split"])

    def test_minor_size_only_returns_advisory(self):
        out = run(heuristic_input(loc=300), skeleton_input(skeleton_loc=180, projected=306), cohesion_input())
        self.assertEqual(out["verdict"], "advisory")
        self.assertEqual(out["size"]["severity"], "MINOR")

    def test_minor_cohesion_only_returns_advisory(self):
        groups = [
            {"label": "A", "acs": ["US-1.1"], "shared_signals": ["x", "y"]},
            {"label": "B", "acs": ["US-2.1"], "shared_signals": ["x", "y"]},
        ]
        out = run(heuristic_input(), skeleton_input(), cohesion_input(group_count=2, severity="MINOR", groups=groups))
        self.assertEqual(out["verdict"], "advisory")

    def test_severe_cohesion_returns_needs_split_with_candidates(self):
        groups = [
            {"label": "Decorator", "acs": ["US-1.1"], "shared_signals": ["x", "y"]},
            {"label": "Policies", "acs": ["US-2.1"], "shared_signals": ["a", "b"]},
            {"label": "Cancel", "acs": ["US-3.1"], "shared_signals": ["c", "d"]},
        ]
        out = run(heuristic_input(), skeleton_input(), cohesion_input(group_count=3, severity="SEVERE", groups=groups))
        self.assertEqual(out["verdict"], "needs_split")
        self.assertEqual(out["split_recommendation"]["driver"], "cohesion")
        self.assertEqual(len(out["split_recommendation"]["candidate_subtasks"]), 3)
        titles = [c["title"] for c in out["split_recommendation"]["candidate_subtasks"]]
        self.assertEqual(titles, ["Decorator", "Policies", "Cancel"])

    def test_severe_size_with_compliant_cohesion_is_oversized_cohesive(self):
        out = run(heuristic_input(loc=500), skeleton_input(skeleton_loc=300, projected=510), cohesion_input())
        self.assertEqual(out["verdict"], "needs_split")
        self.assertEqual(out["split_recommendation"]["driver"], "size")
        self.assertEqual(out["split_recommendation"]["candidate_subtasks"], [])

    def test_severe_size_with_minor_cohesion_drives_cohesion(self):
        """When size is SEVERE and cohesion is MINOR, prefer cohesion as the split driver."""
        groups = [
            {"label": "A", "acs": ["US-1.1"], "shared_signals": ["x", "y"]},
            {"label": "B", "acs": ["US-2.1"], "shared_signals": ["x", "y"]},
        ]
        out = run(heuristic_input(loc=500), skeleton_input(skeleton_loc=300, projected=510),
                  cohesion_input(group_count=2, severity="MINOR", groups=groups))
        self.assertEqual(out["verdict"], "needs_split")
        self.assertEqual(out["split_recommendation"]["driver"], "cohesion")
        self.assertEqual(len(out["split_recommendation"]["candidate_subtasks"]), 2)


class Consensus(unittest.TestCase):
    def test_consensus_takes_max(self):
        out = run(heuristic_input(loc=180), skeleton_input(skeleton_loc=120, projected=204), cohesion_input())
        self.assertEqual(out["size"]["consensus_loc"], 204)

    def test_consensus_when_heuristic_higher(self):
        out = run(heuristic_input(loc=300), skeleton_input(skeleton_loc=100, projected=170), cohesion_input())
        self.assertEqual(out["size"]["consensus_loc"], 300)


class CalibrationDrift(unittest.TestCase):
    def test_drift_below_threshold(self):
        out = run(heuristic_input(loc=200), skeleton_input(skeleton_loc=120, projected=180), cohesion_input())
        self.assertFalse(out["size"]["calibration_drift"])

    def test_drift_above_threshold(self):
        # |200 - 50| / 200 = 0.75 > 0.5
        out = run(heuristic_input(loc=200), skeleton_input(skeleton_loc=30, projected=50), cohesion_input())
        self.assertTrue(out["size"]["calibration_drift"])

    def test_drift_zero_when_equal(self):
        out = run(heuristic_input(loc=180), skeleton_input(skeleton_loc=110, projected=180), cohesion_input())
        self.assertEqual(out["size"]["calibration_delta"], 0.0)
        self.assertFalse(out["size"]["calibration_drift"])

    def test_zero_loc_does_not_divide_by_zero(self):
        out = run(heuristic_input(loc=0), skeleton_input(skeleton_loc=0, projected=0), cohesion_input())
        self.assertEqual(out["size"]["calibration_delta"], 0.0)
        self.assertFalse(out["size"]["calibration_drift"])


class SizeBands(unittest.TestCase):
    def test_band_assignment_for_candidates(self):
        groups = [
            {"label": "G1", "acs": ["US-1.1"], "shared_signals": ["a", "b"]},
            {"label": "G2", "acs": ["US-2.1"], "shared_signals": ["c", "d"]},
            {"label": "G3", "acs": ["US-3.1"], "shared_signals": ["e", "f"]},
        ]
        # consensus_loc 600, 3 groups → 200 LOC each → "medium"
        out = run(heuristic_input(loc=600), skeleton_input(skeleton_loc=350, projected=595),
                  cohesion_input(group_count=3, severity="SEVERE", groups=groups))
        bands = [c["estimated_size_band"] for c in out["split_recommendation"]["candidate_subtasks"]]
        self.assertEqual(bands, ["medium", "medium", "medium"])


class CLIContract(unittest.TestCase):
    def test_missing_input_file_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Only write heuristic; skeleton + cohesion missing
            (Path(tmp) / "heuristic.json").write_text(json.dumps(heuristic_input()), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(tmp)],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_malformed_json_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "heuristic.json").write_text("not json", encoding="utf-8")
            (Path(tmp) / "skeleton.json").write_text(json.dumps(skeleton_input()), encoding="utf-8")
            (Path(tmp) / "cohesion.json").write_text(json.dumps(cohesion_input()), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(tmp)],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_wrong_arg_count_exits_non_zero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
