"""Serializes typed source-search results for the CLI JSON boundary."""

from search.codebase_search_output_serializing import CodebaseSearchOutputSerializing
from search.codebase_search_query_kind import CodebaseSearchQueryKind
from source.source_search_output import SourceSearchOutput

_MISSING_DESCRIPTION = "No solid-description frontmatter."


"""
solid-name: CodebaseSearchOutputSerializer
solid-category: serializer
solid-spec: [SPEC-040]
solid-description: Serializes source candidates and scan totals into CLI-compatible JSON data.
"""
class CodebaseSearchOutputSerializer(CodebaseSearchOutputSerializing):
    def serialize(self, output: SourceSearchOutput) -> dict:
        matches = [
            {
                "unit": candidate.unit,
                "description": candidate.description,
                "path": str(candidate.path),
                "source_identity": candidate.source_identity,
                "content_sha256": candidate.content_sha256,
                "matched_terms": [
                    match.term
                    for match in candidate.matches
                    if match.query_id == CodebaseSearchQueryKind.TERMS.value
                ],
                "matched_specs": [
                    match.term
                    for match in candidate.matches
                    if match.query_id
                    == CodebaseSearchQueryKind.SPECIFICATIONS.value
                ],
            }
            for candidate in output.candidates
        ]
        return {
            "matches": matches,
            "summary": {
                "total_files_scanned": output.files_scanned,
                "files_with_frontmatter": len([
                    candidate
                    for candidate in output.candidates
                    if candidate.description != _MISSING_DESCRIPTION
                ]),
                "files_matched": len(matches),
            },
        }
