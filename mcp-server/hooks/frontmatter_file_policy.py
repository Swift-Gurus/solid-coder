"""
solid-description: Determines file processing eligibility and provides extracted content for tools.
solid-category: service
solid-tags: [hook]
"""

from typing import Optional

from frontmatter_file_filter import FrontmatterFileFilter
from tool_content_extractor import ToolContentExtractor


class FrontmatterFilePolicy:
    """Coordinates ToolContentExtractor and FrontmatterFileFilter behind the FileTypePolicy contract."""

    def __init__(self, content_extractor: ToolContentExtractor, file_filter: FrontmatterFileFilter) -> None:
        self._content_extractor = content_extractor
        self._file_filter = file_filter

    def content_for(self, tool_name: str, tool_input: dict) -> Optional[str]:
        return self._content_extractor.content_for(tool_name, tool_input)

    def should_process(self, file_path: str, content: str) -> bool:
        return self._file_filter.should_process(file_path, content)
