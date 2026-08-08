"""Persists and checks health-check DRY-search completion."""

from harness.atomic_file_writing import AtomicFileWriting
from harness.path_building import PathBuilding
from harness.path_checking import PathChecking
from health.dry_search_completion_status import DrySearchCompletionStatus


"""
solid-name: FileDrySearchCompletionStore
solid-category: service
solid-description: Records and evaluates health-check DRY-search completion state.
"""
class FileDrySearchCompletionStore:
    _HEALTH_INPUT_NAME = "hook-input.json"
    _MARKER_NAME = "dry-search.completed"

    def __init__(
        self,
        path_builder: PathBuilding,
        path_checker: PathChecking,
        marker_writer: AtomicFileWriting,
    ) -> None:
        self._path_builder = path_builder
        self._path_checker = path_checker
        self._marker_writer = marker_writer

    def record(self, output_dir: str) -> None:
        health_input_path = self._path_builder.build(output_dir, self._HEALTH_INPUT_NAME)
        if not self._path_checker.exists(str(health_input_path)):
            return

        marker_path = self._path_builder.build(output_dir, self._MARKER_NAME)
        try:
            self._marker_writer.write_exclusive(marker_path, b"completed\n")
        except FileExistsError:
            return

    def clear(self, output_dir: str) -> None:
        marker_path = self._path_builder.build(output_dir, self._MARKER_NAME)
        marker_path.unlink(missing_ok=True)

    def status(self, output_dir: str) -> DrySearchCompletionStatus:
        health_input_path = self._path_builder.build(output_dir, self._HEALTH_INPUT_NAME)
        if not self._path_checker.exists(str(health_input_path)):
            return DrySearchCompletionStatus.NOT_REQUIRED

        marker_path = self._path_builder.build(output_dir, self._MARKER_NAME)
        if self._path_checker.exists(str(marker_path)):
            return DrySearchCompletionStatus.COMPLETE
        return DrySearchCompletionStatus.MISSING
