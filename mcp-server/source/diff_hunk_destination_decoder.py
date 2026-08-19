"""Decodes destination positions from unified-diff hunk headers."""

from source.diff_hunk_destination_decoding import DiffHunkDestinationDecoding
from source.source_operation_error import SourceOperationError


"""
solid-name: DiffHunkDestinationDecoder
solid-category: boundary
solid-spec: [SPEC-040]
solid-description: Decodes destination start lines from validated unified-diff hunk headers.
"""
class DiffHunkDestinationDecoder(DiffHunkDestinationDecoding):
    def decode(self, header: str) -> int:
        destination = next(
            (component for component in header.split(" ") if component.startswith("+")),
            None,
        )
        if destination is None:
            raise SourceOperationError(f"Invalid unified-diff hunk header: {header}")
        start = destination[1:].split(",", maxsplit=1)[0]
        try:
            return int(start)
        except ValueError as error:
            raise SourceOperationError(
                f"Invalid unified-diff destination line: {header}"
            ) from error
