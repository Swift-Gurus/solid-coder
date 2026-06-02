"""
solid-name: test_fixtures
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Shared reusable test fixtures for the principle test harness test suite.
"""

from __future__ import annotations

from pathlib import Path

from _path_bootstrap import ensure_on_path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_HARNESS_DIR = _PROJECT_ROOT / "tests" / "harness"
_HOOKS_DIR = _PROJECT_ROOT / "hooks"

ensure_on_path(_HARNESS_DIR, _HERE, _HOOKS_DIR)

from models import ModelProfile, OutputPaths  # noqa: E402


def _make_output_paths(tmp_dir: Path) -> OutputPaths:
    log_dir = tmp_dir / "logs"
    return OutputPaths(
        log_dir=log_dir,
        reasoning_path=log_dir / "reasoning.txt",
        review_output_path=log_dir / "review-output.json",
    )


def _make_profile(profile_path: Path | None = None) -> ModelProfile:
    return ModelProfile(
        output_dir_name="test",
        profile_path=profile_path,
        llm={},
        inference={},
    )
