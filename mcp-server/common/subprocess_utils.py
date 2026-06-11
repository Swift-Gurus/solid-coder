#!/usr/bin/env python3
"""
solid-description: Shared helper for executing shell commands and returning their success status and captured output.
solid-category: utility
solid-tags: [utility, service]
"""

import subprocess


def run_cmd(cmd: list) -> tuple[bool, str, str]:
    """Execute a command and return (success, stdout, stderr).

    Args:
        cmd: Command and arguments as a list.

    Returns:
        Tuple of (success, stdout_stripped, stderr_stripped).
    """
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
