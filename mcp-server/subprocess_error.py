"""
solid-description: Exception indicating failure of a subprocess operation.
solid-category: model
"""


class SubprocessError(Exception):
    """Raised when a gate subprocess fails. Carries the reason for display."""