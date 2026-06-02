"""
solid-name: OutputPathBuilder
solid-category: utility
solid-spec: [SPEC-014]
solid-description: Resolves and provisions a set of output paths for a principle test harness run given its identifying coordinates.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from interfaces import OutputPathBuilding  # noqa: E402
from models import OutputPaths  # noqa: E402


class OutputPathBuilder(OutputPathBuilding):
    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root

    def build(
        self,
        run_timestamp: str,
        model_name: str,
        category_path: str,
        fixture_stem: str,
        flow_name: str,
    ) -> OutputPaths:
        log_dir = (
            self._project_root
            / ".solid-coder"
            / "logs"
            / "tests"
            / run_timestamp
            / model_name
            / category_path
        )
        log_dir.mkdir(parents=True, exist_ok=True)
        base_name = f"{fixture_stem}-{flow_name}"
        reasoning_path = log_dir / f"{base_name}.txt"
        review_output_path = log_dir / f"{base_name}-review-output.json"
        return OutputPaths(
            log_dir=log_dir,
            reasoning_path=reasoning_path,
            review_output_path=review_output_path,
        )
