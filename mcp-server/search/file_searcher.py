"""Locates source files by type name or filename pattern."""

import re

from harness.path_building import PathBuilding
from harness.project_context import ProjectDirectoryReading
from source.default_source_file_extensions import DEFAULT_SOURCE_FILE_EXTENSIONS
from source.repository_source_files_discovering import RepositorySourceFilesDiscovering
from utils.path_file_system_reader import FileSystemReading

"""
solid-name: FileSearcher
solid-category: service
solid-spec: [SPEC-040, SPEC-060]
solid-description: Finds source definitions by declared type name and locates source files by filename pattern within a project.
"""


class FileSearcher:
    def __init__(
        self,
        files: RepositorySourceFilesDiscovering,
        file_system: FileSystemReading,
        project_directory: ProjectDirectoryReading,
        paths: PathBuilding,
    ) -> None:
        self._files = files
        self._file_system = file_system
        self._project_directory = project_directory
        self._paths = paths

    def grep_by_name(self, name: str, directory: str | None = None) -> str:
        root = (
            self._paths.build(directory)
            if directory
            else self._project_directory.read()
        )
        if not self._file_system.is_dir(str(root)):
            return f"Error: directory not found: {root}"
        pattern = re.compile(
            r"\b(class|struct|protocol|enum|actor|extension|typealias)\s+"
            + re.escape(name)
            + r"\b"
        )
        results: list[str] = []
        for filepath in self._files.discover(root):
            if filepath.suffix not in DEFAULT_SOURCE_FILE_EXTENSIONS:
                continue
            try:
                content = self._file_system.read_text(filepath)
                results.extend(
                    f"{filepath}:{lineno}: {line.strip()}"
                    for lineno, line in enumerate(content.splitlines(), 1)
                    if pattern.search(line)
                )
            except (OSError, UnicodeError):
                continue
        return (
            "\n".join(results)
            if results
            else f"No definitions or extensions of '{name}' found."
        )

    def glob_by_name(self, pattern: str, directory: str | None = None) -> str:
        root = (
            self._paths.build(directory)
            if directory
            else self._project_directory.read()
        )
        if not self._file_system.is_dir(str(root)):
            return f"Error: directory not found: {root}"
        matches = sorted(
            str(path) for path in self._files.discover(root) if path.match(pattern)
        )
        return (
            "\n".join(matches) if matches else f"No files matching '{pattern}' found."
        )
