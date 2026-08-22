"""
solid-name: HealthCheckInputWriting
solid-category: abstraction
solid-description: Contract for writing language-identified content to a specified file location.
"""

from typing import Optional, Protocol

from patch_review_context import PatchReviewContext


class HealthCheckInputWriting(Protocol):

    def write(
        self,
        output_dir: str,
        file_path: str,
        language: str,
        content: str,
        patch_context: Optional[PatchReviewContext] = None,
    ) -> None: ...
