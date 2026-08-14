"""Retrieves specification ancestry through the installed query script."""

from pathlib import Path
from typing import Callable

from spec_ancestry_retrieving import SpecAncestryRetrieving
from subprocess_running import SubprocessRunning


"""
solid-name: SpecAncestryRetriever
solid-category: boundary-adapter
solid-description: Retrieves specification ancestry records from the configured query capability.
"""
class SpecAncestryRetriever(SpecAncestryRetrieving):
    def __init__(
        self,
        script: Path,
        executable: str,
        process: SubprocessRunning,
        deserializer: Callable[[str], object],
    ) -> None:
        self._script = script
        self._executable = executable
        self._process = process
        self._deserialize = deserializer

    def retrieve(self, spec_number: str, blocked: bool) -> list[dict]:
        command = [self._executable, str(self._script), "ancestors", spec_number]
        if blocked:
            command.append("--blocked")
        succeeded, output, error = self._process.run(command)
        if not succeeded:
            raise RuntimeError(error)
        specs = self._deserialize(output)
        return specs if isinstance(specs, list) else []
