"""
solid-description: Verifies gateway commands retain the active interpreter, arguments, timeout, and response handling.
solid-category: unit-test
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

from health.gateway.gateway_command_runner import GatewayCommandRunner
from hook_utils import SubprocessError, SubprocessJsonRunning


class TestGatewayCommandRunner(unittest.TestCase):
    def test_invoke_uses_constructor_timeout(self):
        runner = Mock(spec=SubprocessJsonRunning)
        runner.run.return_value = {"content": "x"}
        invoker = GatewayCommandRunner(Path("/gateway.py"), timeout=123, runner=runner)
        invoker.invoke("get_candidate_tags")
        runner.run.assert_called_once_with(
            [sys.executable, "/gateway.py", "get_candidate_tags"], timeout=123
        )

    def test_different_instances_can_use_different_timeouts(self):
        runner_a = Mock(spec=SubprocessJsonRunning)
        runner_b = Mock(spec=SubprocessJsonRunning)
        GatewayCommandRunner(Path("/gateway.py"), timeout=5, runner=runner_a).invoke("cmd")
        GatewayCommandRunner(Path("/gateway.py"), timeout=999, runner=runner_b).invoke("cmd")
        self.assertEqual(runner_a.run.call_args.kwargs["timeout"], 5)
        self.assertEqual(runner_b.run.call_args.kwargs["timeout"], 999)

    def test_injected_executable_and_arguments_remain_separate(self):
        runner = Mock(spec=SubprocessJsonRunning)
        invoker = GatewayCommandRunner(
            Path("/plugin with spaces/gateway.py"), timeout=30, runner=runner,
            executable="/runtime with spaces/bin/python3.12",
        )

        invoker.invoke("load_detection_rules", extra_args=["--matched_tags", "swiftui"])

        runner.run.assert_called_once_with(
            ["/runtime with spaces/bin/python3.12", "/plugin with spaces/gateway.py",
             "load_detection_rules", "--matched_tags", "swiftui"],
            timeout=30,
        )

    def test_selects_requested_response_field(self):
        runner = Mock(spec=SubprocessJsonRunning)
        runner.run.return_value = {"candidate_tags": ["swiftui"]}
        invoker = GatewayCommandRunner(Path("/gateway.py"), timeout=30, runner=runner)

        self.assertEqual(invoker.invoke("get_candidate_tags", result_key="candidate_tags"), ["swiftui"])

    def test_absent_response_or_field_uses_default(self):
        runner = Mock(spec=SubprocessJsonRunning)
        invoker = GatewayCommandRunner(Path("/gateway.py"), timeout=30, runner=runner)

        for response in (None, {}):
            with self.subTest(response=response):
                runner.run.return_value = response
                self.assertEqual(invoker.invoke("get_candidate_tags", result_key="candidate_tags", default=[]), [])

    def test_propagates_subprocess_failure(self):
        runner = Mock(spec=SubprocessJsonRunning)
        runner.run.side_effect = SubprocessError("gateway failed")
        invoker = GatewayCommandRunner(Path("/gateway.py"), timeout=30, runner=runner)

        with self.assertRaisesRegex(SubprocessError, "gateway failed"):
            invoker.invoke("get_candidate_tags")


if __name__ == "__main__":
    unittest.main()
