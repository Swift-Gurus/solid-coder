"""Checks the preserved legacy verification harness can read its disabled skill prompt."""

import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS))

from apply_flow_invoker import _build_skill_prompt


def test_archived_prompt_still_builds_for_explicit_legacy_verification(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[3]
    prompt = _build_skill_prompt(
        root,
        root / "references/principles/SRP",
        tmp_path / "review-input.json",
        tmp_path / "output",
        "parent",
    )

    assert prompt.startswith("# spawned-by: parent")
    assert "mcp__pipeline__submit_batch_findings" in prompt
    assert "mcp__docs__load_detection_rules" in prompt
    assert "${CLAUDE_PLUGIN_ROOT}" not in prompt
    assert str(tmp_path / "review-input.json") in prompt
