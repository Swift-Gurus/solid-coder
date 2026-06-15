"""solid-description: Defines the standard file and directory paths for configuration.
solid-category: utility
solid-tags: [hook, utility]

Change these constants — not the consumers — when renaming config files or moving the config dir.
"""

CONFIG_DIR        = ".solid-coder"       # directory at project root; its presence marks the root
CONFIG_TOML       = "config.toml"        # committed shared config; existence is the root marker
CONFIG_LOCAL_TOML = "config.local.toml"  # per-user overrides, not committed
SEVERITY_BANDS    = "severity-bands.yml" # per-principle threshold overrides
