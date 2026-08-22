"""Adapts content inspection into frontmatter-description detection."""

from utils.hook_callable import CallableAdapting


"""
solid-name: CallableFrontmatterDescriptionDetector
solid-category: utility
solid-description: Detects authored frontmatter descriptions through an injected content-inspection capability.
solid-tags: [hook]
"""
class CallableFrontmatterDescriptionDetector(CallableAdapting):
    def detects(self, content: str) -> bool:
        return bool(self._strict_call(content))
