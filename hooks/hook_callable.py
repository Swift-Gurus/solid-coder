"""
solid-description: Shared base for callable adapters used throughout the hook layer.
solid-category: utility
solid-tags: [hook, utility]
"""


class CallableAdapting:
    """Base for callable adapters — stores an injected callable and delegates to it.

    Subclasses add domain-specific method signatures and any bound configuration,
    then delegate to self._fn with the appropriate arguments.
    """

    def __init__(self, fn) -> None:
        self._fn = fn
