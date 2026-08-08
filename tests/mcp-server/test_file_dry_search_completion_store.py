"""Verifies health-check DRY-search completion persistence."""

from pathlib import Path

from harness.path_builder import PathBuilder
from harness.path_checking import PathChecker
from harness.posix_atomic_file_writer import POSIXAtomicFileWriter
from health.dry_search_completion_status import DrySearchCompletionStatus
from health.file_dry_search_completion_store import FileDrySearchCompletionStore


"""
solid-name: TestFileDrySearchCompletionStore
solid-category: unit-test
solid-description: Verifies health-check DRY-search completion is recorded and evaluated consistently.
"""
class TestFileDrySearchCompletionStore:
    def test_non_health_directory_does_not_require_completion(self, tmp_path: Path) -> None:
        store = self._make_store()

        assert store.status(str(tmp_path)) is DrySearchCompletionStatus.NOT_REQUIRED

    def test_non_health_directory_does_not_record_completion(self, tmp_path: Path) -> None:
        store = self._make_store()

        store.record(str(tmp_path))

        assert not (tmp_path / "dry-search.completed").exists()

    def test_health_directory_without_completion_is_missing(self, tmp_path: Path) -> None:
        self._write_health_input(tmp_path)
        store = self._make_store()

        assert store.status(str(tmp_path)) is DrySearchCompletionStatus.MISSING

    def test_recorded_health_directory_is_complete(self, tmp_path: Path) -> None:
        self._write_health_input(tmp_path)
        store = self._make_store()

        store.record(str(tmp_path))

        assert store.status(str(tmp_path)) is DrySearchCompletionStatus.COMPLETE

    def test_recording_completion_twice_is_idempotent(self, tmp_path: Path) -> None:
        self._write_health_input(tmp_path)
        store = self._make_store()

        store.record(str(tmp_path))
        store.record(str(tmp_path))

        assert store.status(str(tmp_path)) is DrySearchCompletionStatus.COMPLETE

    def test_clearing_reused_health_directory_invalidates_completion(self, tmp_path: Path) -> None:
        self._write_health_input(tmp_path)
        store = self._make_store()
        store.record(str(tmp_path))

        store.clear(str(tmp_path))

        assert store.status(str(tmp_path)) is DrySearchCompletionStatus.MISSING

    @staticmethod
    def _make_store() -> FileDrySearchCompletionStore:
        return FileDrySearchCompletionStore(
            path_builder=PathBuilder(),
            path_checker=PathChecker(),
            marker_writer=POSIXAtomicFileWriter(),
        )

    @staticmethod
    def _write_health_input(output_dir: Path) -> None:
        (output_dir / "hook-input.json").write_text("{}\n", encoding="utf-8")
