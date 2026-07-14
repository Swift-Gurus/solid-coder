"""
solid-description: Exception raised when project configuration fails schema validation.
solid-category: model
"""


class SolidCoderConfigError(ValueError):
    """Raised when config.toml / config.local.toml fails validation. Carries a field-level message."""