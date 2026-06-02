"""
solid-name: interfaces
solid-category: abstraction
solid-spec: [SPEC-014]
solid-description: Contract that defines the composable interface boundaries for each stage of a principle test harness pipeline.
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from models import (  # noqa: E402
    DiffEntry,
    ExpectedFinding,
    Expectation,
    FixturePair,
    ModelProfile,
    OutputPaths,
)


class TomlLoading(ABC):
    @abstractmethod
    def load_toml(self, path: Path) -> dict: ...


class ClaudeRunning(ABC):
    @abstractmethod
    def run_bare(
        self,
        prompt: str,
        allowed_tools: str,
        mcp_config: str,
        timeout: int,
        session_id: str,
    ) -> str | None: ...


class PathResolving(ABC):
    @abstractmethod
    def resolve(self, references_path: str) -> Path: ...


class FixtureDiscovering(ABC):
    @abstractmethod
    def discover(self, tests_path: Path) -> list[FixturePair]: ...


class ExpectationLoading(ABC):
    @abstractmethod
    def load(self, expectation_path: Path) -> Expectation: ...


class ModelProfileLoading(ABC):
    @abstractmethod
    def load(self, model_name: str | None) -> ModelProfile: ...


class OutputPathBuilding(ABC):
    @abstractmethod
    def build(
        self,
        run_timestamp: str,
        model_name: str,
        category_path: str,
        fixture_stem: str,
        flow_name: str,
    ) -> OutputPaths: ...


class FindingComparing(ABC):
    @abstractmethod
    def compare(self, expected: list[ExpectedFinding], actual: list[dict]) -> list[DiffEntry]: ...


class ResultFormatting(ABC):
    @abstractmethod
    def format_status(self, passed: bool, model: str, category_path: str, stem: str, flow: str) -> str: ...

    @abstractmethod
    def format_failures(self, diffs: list[DiffEntry], reasoning_path: Path) -> list[str]: ...


class FlowInvoking(ABC):
    @abstractmethod
    def invoke(
        self,
        fixture_path: Path,
        output_paths: OutputPaths,
        model_profile: ModelProfile,
        timeout: int,
    ) -> list[dict]: ...


class TimestampGenerating(ABC):
    @abstractmethod
    def now_str(self) -> str: ...


class TestHarnessRunning(ABC):
    @abstractmethod
    def run(
        self,
        principle_path: str,
        flow: str | None,
        fixture_filter: str | None,
        model_name: str | None,
        timeout: int,
    ) -> bool: ...


class ReviewArtifactHandling(ABC):
    @abstractmethod
    def build_input(self, fixture_path: Path, log_dir: Path) -> Path: ...

    @abstractmethod
    def write_reasoning(self, path: Path, content: str) -> None: ...

    @abstractmethod
    def read_findings(self, path: Path) -> list[dict]: ...


class ReviewSessionExecuting(ABC):
    @abstractmethod
    def execute(
        self,
        principle_folder: Path,
        review_input_path: Path,
        output_path: Path,
        timeout: int,
    ) -> str | None: ...


class McpConfigBuilding(ABC):
    @abstractmethod
    def build(self, project_root: Path) -> str: ...


class SupportedExtensionsProviding(ABC):
    @abstractmethod
    def get_language(self, suffix: str) -> str: ...


class FindingNormalizing(ABC):
    """Normalizes expected and actual findings into comparable shapes per flow."""

    @abstractmethod
    def normalize(
        self,
        flow_name: str,
        expected: list[ExpectedFinding],
        actual: list[dict],
    ) -> tuple[list[ExpectedFinding], list[dict]]: ...


class CheckResultWriting(ABC):
    @abstractmethod
    def write(self, result: list[dict], output_paths: OutputPaths) -> None: ...
