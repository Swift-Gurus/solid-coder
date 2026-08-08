"""
solid-description: Records subprocess invocation for test assertion while returning a controlled value.
solid-category: unit-test
"""


class CaptureRunner:
    """Captures the subprocess cmd and cwd for assertion in tests."""

    def __init__(self, return_value):
        self.captured_cmd = None
        self.captured_cwd = None
        self._return_value = return_value

    def run(self, cmd, timeout=None, stdin=None, cwd=None):
        self.captured_cmd = cmd
        self.captured_cwd = cwd
        return self._return_value
