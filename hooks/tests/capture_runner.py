"""
solid-description: Test double that captures command arguments for test assertion.
solid-category: unit-test
"""


class CaptureRunner:
    """Captures the subprocess cmd for assertion in tests."""

    def __init__(self, return_value):
        self.captured_cmd = None
        self._return_value = return_value

    def run(self, cmd, timeout=None, stdin=None):
        self.captured_cmd = cmd
        return self._return_value
