"""
solid-description: Aggregates code review violations across principles to produce a severity verdict.
solid-category: service
solid-tags: [pipeline, service]
"""

import json
from pathlib import Path
from typing import Callable, Optional, Protocol

from findings.severity_summariser import SeveritySummarising, SeveritySummariser
from pipeline.interfaces import ReviewResultsCollecting  # noqa: F401 — re-exported for callers


FileGlobbing = Callable[[Path, str], list]
FileReading = Callable[[Path], Optional[dict]]


def _default_glob(directory: Path, pattern: str) -> list:
    return sorted(directory.glob(pattern))


def _default_read(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


class ReviewFileFinding(Protocol):
    def find(self, principle_dir: Path) -> Optional[Path]: ...
    def read(self, principle_dir: Path) -> tuple: ...


class ReviewFileFinder:
    """Locates and parses the review-output.json for a single principle directory.

    Handles both the nested layout (rules/{p}/{p}/review-output.json) and the
    direct layout (rules/{p}/review-output.json) so older and newer pipeline
    outputs are both supported.
    """

    def __init__(
        self,
        glob_fn: Optional[FileGlobbing] = None,
        read_fn: Optional[FileReading] = None,
    ) -> None:
        self._glob = glob_fn or _default_glob
        self._read = read_fn or _default_read

    def find(self, principle_dir: Path) -> Optional[Path]:
        """Return the review-output.json path, or None if absent."""
        nested = self._glob(principle_dir, "*/review-output.json")
        if nested:
            return nested[0]
        direct = principle_dir / "review-output.json"
        return direct if direct.exists() else None

    def read(self, principle_dir: Path) -> tuple:
        """Return (path, data_dict) or (None, None) if not found or unreadable."""
        path = self.find(principle_dir)
        if path is None:
            return None, None
        return path, self._read(path)


class ReviewResultsCollector:
    """Facade: aggregates per-principle review outputs into a severity verdict.

    Delegates file discovery to ReviewFileFinding and severity counting to
    SeveritySummarising. OCP Facade exception applies.
    """

    def __init__(
        self,
        file_finder: ReviewFileFinding,
        summariser: SeveritySummarising,
    ) -> None:
        self._finder = file_finder
        self._summariser = summariser

    def collect(self, output_root: str) -> dict:
        rules_dir = Path(output_root) / "rules"
        if not rules_dir.is_dir():
            return {"error": f"No rules/ directory found in {output_root}. Have reviews completed?"}

        table = []
        minor_violations: list = []

        for principle_dir in sorted(rules_dir.iterdir()):
            if not principle_dir.is_dir():
                continue

            review_path, data = self._finder.read(principle_dir)
            if review_path is None:
                continue

            if data is None:
                table.append({
                    "principle": principle_dir.name,
                    "severity": "ERROR",
                    "violations": 0,
                    "path": str(review_path),
                    "error": "failed to read or parse review output",
                })
                continue

            files = data.get("files", [])
            summary = self._summariser.summarise(files)
            minor_violations.extend(self._minor_from(files))

            table.append({
                "principle": principle_dir.name,
                "severity": summary["status"],
                "violations": summary["severe_count"] + summary["minor_count"],
                "severe": summary["severe_count"],
                "minor": summary["minor_count"],
                "path": str(review_path),
            })

        if not table:
            return {"verdict": "ALL_COMPLIANT", "summary": [], "minor_violations": []}

        has_severe = any(r.get("severity") == "SEVERE" for r in table)
        has_minor = any(r.get("minor", 0) > 0 for r in table)
        verdict = "HAS_SEVERE" if has_severe else ("MINOR_ONLY" if has_minor else "ALL_COMPLIANT")
        return {
            "verdict": verdict,
            "summary": table,
            "minor_violations": minor_violations,
            "total_severe": sum(r.get("severe", 0) for r in table),
            "total_minor": sum(r.get("minor", 0) for r in table),
        }

    def _minor_from(self, files: list) -> list:
        return [
            v
            for f in files
            for unit in f.get("units", [])
            for v in unit.get("violations", [])
            if v.get("severity") == "MINOR"
        ]


def make_review_results_collector() -> ReviewResultsCollector:
    """Wire production defaults."""
    return ReviewResultsCollector(
        file_finder=ReviewFileFinder(),
        summariser=SeveritySummariser(),
    )
