"""
solid-name: models
solid-category: model
solid-spec: [SPEC-014]
solid-description: Data models representing fixture inputs, expected code-quality findings, diff results, and output configuration for the principle test harness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FixturePair:
    fixture_path: Path
    expectation_path: Path
    stem: str


@dataclass
class ExpectedFinding:
    unit_name: str
    metric_id: str
    severity: str
    metrics: dict | None = None


@dataclass
class Expectation:
    findings: list[ExpectedFinding] = field(default_factory=list)


@dataclass
class DiffEntry:
    kind: str
    unit_name: str
    metric_id: str
    severity: str
    metric_key: str | None = None
    expected_value: object | None = None
    actual_value: object | None = None


@dataclass
class ModelProfile:
    output_dir_name: str
    profile_path: Path | None
    llm: dict
    inference: dict


@dataclass
class OutputPaths:
    log_dir: Path
    reasoning_path: Path
    review_output_path: Path
