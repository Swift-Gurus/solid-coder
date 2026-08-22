"""Adapts path-name extraction into write-gate file-name resolution."""

from utils.hook_callable import CallableAdapting


"""
solid-name: CallableFileNameResolver
solid-category: utility
solid-description: Resolves display file names through an injected path-name capability.
solid-tags: [hook]
"""
class CallableFileNameResolver(CallableAdapting):
    def resolve(self, file_path: str) -> str:
        return self._strict_call(file_path)
