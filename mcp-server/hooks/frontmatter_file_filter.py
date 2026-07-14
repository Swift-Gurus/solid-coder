"""
solid-description: Filters files for processing based on supported extensions and required content markers.
solid-category: service
solid-tags: [hook]
"""

from typing import Optional, Set

from path_extracting import PathExtracting

_SUPPORTED_EXTENSIONS = {".swift", ".py"}


class FrontmatterFileFilter:
    """In scope when the extension is supported and the content has the required frontmatter field."""

    def __init__(
        self,
        path_extractor: PathExtracting,
        field_marker: str = "solid-description:",
        supported_extensions: Optional[Set[str]] = None,
    ) -> None:
        self._path_extractor = path_extractor
        self._field_marker = field_marker
        self._supported_extensions = supported_extensions if supported_extensions is not None else _SUPPORTED_EXTENSIONS

    def should_process(self, file_path: str, content: str) -> bool:
        ext = self._path_extractor.suffix_of(file_path)
        return ext in self._supported_extensions and self._field_marker in content
