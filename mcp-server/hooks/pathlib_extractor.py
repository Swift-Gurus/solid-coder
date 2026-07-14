"""
solid-description: Extracts the lowercased file extension from file paths.
solid-category: service
solid-tags: [hook]
"""

from hook_callable import CallableAdapting


class PathlibExtractor(CallableAdapting):
    """Extracts the lowercased file extension via an injected suffix-extraction callable."""

    def suffix_of(self, file_path: str) -> str:
        return self._strict_call(file_path)
