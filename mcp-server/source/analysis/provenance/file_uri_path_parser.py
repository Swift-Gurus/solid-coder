"""Interprets local file URIs without fetching remote resources."""

from pathlib import Path
from urllib.parse import unquote

from pydantic import FileUrl
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing

"""
solid-name: FileUriPathParser
solid-category: boundary-adapter
solid-spec: [SPEC-064]
solid-description: Resolves a local file URI to its decoded filesystem path.
"""


class FileUriPathParser(SourceSyntaxParsing[FileUrl, Path | None]):
    def parse(self, source: FileUrl) -> Path | None:
        if source.host not in {None, "", "localhost"} or source.path is None:
            return None
        return Path(unquote(source.path))
