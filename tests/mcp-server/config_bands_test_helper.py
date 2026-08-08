"""
solid-description: Test helper for scoring unit metrics in isolated temporary projects.
solid-category: unit-test
"""

import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mcp-server"))

from config_test_writer import ConfigTestWriter


class ConfigBandsTestHelper:
    """Creates an isolated temp project with config and scores a nested source file.

    Accepts injected writer and scorer_factory so each call site controls its
    own concrete implementations without re-wiring from scratch.
    """

    def __init__(
        self,
        writer: ConfigTestWriter,
        scorer_factory: Callable,
    ) -> None:
        self._writer = writer
        self._scorer_factory = scorer_factory

    def score_in_temp_project(
        self,
        rule_path: Path,
        config: dict,
        unit_metrics: dict,
        metric_id: str,
        project_root_override: Optional[str] = None,
    ) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src" / "Foo.swift"
            src.parent.mkdir()
            self._writer.write(Path(tmp), config)
            root = project_root_override if project_root_override is not None else tmp
            scorer = self._scorer_factory(rule_path.parent, project_root=root or None)
            return scorer.score_unit(unit_metrics, metric_id, str(src))

    def write_at(self, directory: Path, content: dict) -> None:
        self._writer.write(directory, content)
