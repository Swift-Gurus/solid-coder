"""
solid-description: Verifies GatewayInvoker always uses its configured timeout for gateway CLI calls.
solid-category: unit-test
"""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from hc_rule_loader import GatewayInvoker  # noqa: E402


class _RecordingRunner:
    def __init__(self, result=None):
        self.result = result
        self.calls = []

    def run_cmd(self, cmd, timeout):
        self.calls.append((cmd, timeout))
        return self.result


class TestGatewayInvoker(unittest.TestCase):
    def test_invoke_uses_constructor_timeout(self):
        runner = _RecordingRunner(result={"content": "x"})
        invoker = GatewayInvoker(Path("/gateway.py"), runner, timeout=123)
        invoker.invoke("get_candidate_tags")
        self.assertEqual(runner.calls[0][1], 123)

    def test_different_instances_can_use_different_timeouts(self):
        runner_a = _RecordingRunner(result={})
        runner_b = _RecordingRunner(result={})
        GatewayInvoker(Path("/gateway.py"), runner_a, timeout=5).invoke("cmd")
        GatewayInvoker(Path("/gateway.py"), runner_b, timeout=999).invoke("cmd")
        self.assertEqual(runner_a.calls[0][1], 5)
        self.assertEqual(runner_b.calls[0][1], 999)


if __name__ == "__main__":
    unittest.main()
