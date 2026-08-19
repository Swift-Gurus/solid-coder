"""Parses stable paths from NUL-delimited command output."""

from source.nul_delimited_paths_parsing import NulDelimitedPathsParsing


"""
solid-name: NulDelimitedPathsParser
solid-category: boundary
solid-spec: [SPEC-040]
solid-description: Parses and orders project-relative paths from NUL-delimited command output.
"""
class NulDelimitedPathsParser(NulDelimitedPathsParsing):
    def parse(self, output: str) -> list[str]:
        return sorted(path for path in output.split("\0") if path)
