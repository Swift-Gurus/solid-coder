#!/usr/bin/env python3
"""Merge heuristic.json, skeleton.json, and cohesion.json into scope-assessment.json.

Usage:
    synthesize-scope.py <output-dir>

Reads the three measurement JSONs from <output-dir> and writes scope-assessment.json
to the same directory. Pure deterministic logic — no LLM, no judgment.
"""
import json
import sys
from pathlib import Path

MINOR_THRESHOLD = 200
SEVERE_THRESHOLD = 400
CALIBRATION_DRIFT_RATIO = 0.5

SIZE_BAND_TINY = 50
SIZE_BAND_SMALL = 150
SIZE_BAND_MEDIUM = 300


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error: required input not found: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"error: malformed JSON in {path}: {e}", file=sys.stderr)
        sys.exit(2)


def severity_for_loc(loc: int) -> str:
    if loc > SEVERE_THRESHOLD:
        return "SEVERE"
    if loc >= MINOR_THRESHOLD:
        return "MINOR"
    return "COMPLIANT"


def estimated_size_band(loc: int) -> str:
    if loc < SIZE_BAND_TINY:
        return "tiny"
    if loc < SIZE_BAND_SMALL:
        return "small"
    if loc < SIZE_BAND_MEDIUM:
        return "medium"
    return "large"


def synthesize(heuristic: dict, skeleton: dict, cohesion: dict) -> dict:
    heuristic_loc = heuristic.get("predicted_loc", 0)
    skeleton_loc = skeleton.get("skeleton_loc", 0)
    skeleton_projected = skeleton.get("projected_loc", 0)

    consensus_loc = max(heuristic_loc, skeleton_projected)

    if consensus_loc == 0:
        calibration_delta = 0.0
    else:
        calibration_delta = abs(heuristic_loc - skeleton_projected) / consensus_loc
    calibration_drift = calibration_delta > CALIBRATION_DRIFT_RATIO

    size_severity = severity_for_loc(consensus_loc)
    cohesion_severity = cohesion.get("severity", "COMPLIANT")
    cohesion_groups = cohesion.get("groups", [])
    cohesion_group_count = cohesion.get("group_count", len(cohesion_groups))

    # Verdict + driver
    if cohesion_severity == "SEVERE":
        verdict = "needs_split"
        driver = "cohesion"
    elif size_severity == "SEVERE":
        verdict = "needs_split"
        driver = "cohesion" if cohesion_severity == "MINOR" else "size"
    elif size_severity == "MINOR" or cohesion_severity == "MINOR":
        verdict = "advisory"
        driver = "none"
    else:
        verdict = "compliant"
        driver = "none"

    # Candidate subtasks
    candidate_subtasks: list[dict] = []
    if driver == "cohesion" and cohesion_group_count > 0:
        per_group_loc = consensus_loc // cohesion_group_count if cohesion_group_count else 0
        for group in cohesion_groups:
            candidate_subtasks.append({
                "title": group.get("label", "Unlabelled group"),
                "acs": group.get("acs", []),
                "estimated_size_band": estimated_size_band(per_group_loc),
            })
    # driver == "size" or "none" → empty candidate_subtasks

    return {
        "verdict": verdict,
        "size": {
            "heuristic_loc": heuristic_loc,
            "skeleton_loc": skeleton_loc,
            "skeleton_projected_loc": skeleton_projected,
            "consensus_loc": consensus_loc,
            "severity": size_severity,
            "calibration_drift": calibration_drift,
            "calibration_delta": round(calibration_delta, 3),
        },
        "cohesion": {
            "group_count": cohesion_group_count,
            "severity": cohesion_severity,
            "groups": cohesion_groups,
        },
        "split_recommendation": {
            "should_split": verdict == "needs_split",
            "driver": driver,
            "candidate_subtasks": candidate_subtasks,
        },
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <output-dir>", file=sys.stderr)
        return 2

    out_dir = Path(sys.argv[1])
    if not out_dir.is_dir():
        print(f"error: output directory does not exist: {out_dir}", file=sys.stderr)
        return 2

    heuristic = load_json(out_dir / "heuristic.json")
    skeleton = load_json(out_dir / "skeleton.json")
    cohesion = load_json(out_dir / "cohesion.json")

    assessment = synthesize(heuristic, skeleton, cohesion)

    output_path = out_dir / "scope-assessment.json"
    output_path.write_text(json.dumps(assessment, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(assessment, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
