"""Verifies new health inputs invalidate prior DRY-search completion."""

from unittest.mock import MagicMock

from health.health_check_input_writer import HealthCheckInputWriter
from patch_file_simulation import PatchFileSimulation
from patch_review_context import PatchReviewContext


"""
solid-name: TestHealthCheckInputWriter
solid-category: unit-test
solid-description: Verifies starting a health-input generation clears prior DRY-search completion proof.
"""
class TestHealthCheckInputWriter:
    def setup_method(self) -> None:
        self.extractor = MagicMock()
        self.writer = MagicMock()
        self.directory = MagicMock()
        self.completion = MagicMock()
        self.input_writer = HealthCheckInputWriter(
            extractor=self.extractor,
            writer=self.writer,
            dir_creator=self.directory,
            completion=self.completion,
        )

    def test_write_clears_completion_for_requested_output_directory(self) -> None:
        self.extractor.extract.return_value = ["Foo"]

        self.input_writer.write(
            output_dir="/health/reused",
            file_path="/src/Foo.swift",
            language="Swift",
            content="class Foo {}",
        )

        self.completion.clear.assert_called_once_with("/health/reused")

    def test_write_persists_every_proposed_patch_source_for_mcp_context(self) -> None:
        self.extractor.extract.return_value = ["First"]
        context = PatchReviewContext(proposed_files=[
            PatchFileSimulation(
                file_path="/src/First.swift",
                content="struct First {}",
                existing_content="",
                low_risk=False,
            ),
            PatchFileSimulation(
                file_path="/src/Second.swift",
                content="struct Second {}",
                existing_content="",
                low_risk=False,
            ),
        ])

        self.input_writer.write(
            output_dir="/health/patch",
            file_path="/src/First.swift",
            language="Swift",
            content="struct First {}",
            patch_context=context,
        )

        persisted = self.writer.write.call_args.args[1]
        assert persisted["proposed_files"] == [
            {"file_path": "/src/First.swift", "content": "struct First {}"},
            {"file_path": "/src/Second.swift", "content": "struct Second {}"},
        ]
