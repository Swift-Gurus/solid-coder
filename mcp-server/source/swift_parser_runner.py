"""Executes the Swift parser against isolated temporary source text."""

from pathlib import Path

from common.temporary_directory_providing import TemporaryDirectoryProviding
from findings.text_file_writing import TextFileWriting
from harness.process_execution_running import ProcessExecutionRunning
from harness.script_execution_result import ScriptExecutionResult
from source.swift_parser_execution import SwiftParserExecution
from source.swift_parser_running import SwiftParserRunning

_SWIFT_PARSE_TIMEOUT_SECONDS = 30


"""
solid-name: SwiftParserRunner
solid-category: boundary-adapter
solid-spec: [SPEC-040]
solid-description: Executes deterministic Swift parsing against isolated source content.
"""
class SwiftParserRunner(SwiftParserRunning):
    def __init__(
        self,
        directories: TemporaryDirectoryProviding,
        writer: TextFileWriting,
        process_runner: ProcessExecutionRunning,
    ) -> None:
        self._directories = directories
        self._writer = writer
        self._process_runner = process_runner

    def run(self, source: str) -> ScriptExecutionResult:
        with self._directories.provide() as directory:
            source_path = Path(directory) / "Analysis.swift"
            self._writer.write(source_path, source)
            return self._process_runner.run(
                SwiftParserExecution(source_path),
                timeout_seconds=_SWIFT_PARSE_TIMEOUT_SECONDS,
                working_directory=directory,
            )
