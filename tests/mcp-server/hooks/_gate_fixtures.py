"""
solid-description: Provides test data and utilities for the pre_write_gate test suite.
solid-category: unit-test
"""

import pre_write_gate as gate
import test_utils

LONG_SWIFT = test_utils.LONG_SWIFT
SHORT_SWIFT = test_utils.SHORT_SWIFT

LONG_SWIFT_WITH_FRONTMATTER = (
    "/**\n solid-name: Foo\n solid-category: service\n"
    " solid-description: Loads data using URLSession.shared.\n */\n"
    "final class Foo {\n" + "    func bar() {}\n" * 35 + "}\n"
)
CORRECTED_FRONTMATTER = (
    "/**\n solid-name: Foo\n solid-category: service\n"
    " solid-description: Coordinates asynchronous data retrieval.\n */\n"
    "final class Foo {\n" + "    func bar() {}\n" * 35 + "}\n"
)
VIOLATIONS = [{"principle": "SRP", "issue": "Two concerns.", "fix": "Extract."}]

PYTHON_CONTENT = (
    "class DataManager:\n"
    "    def read_file(self, path):\n"
    "        with open(path) as f:\n"
    "            return f.read()\n"
    "    def send_request(self, url):\n"
    "        import urllib.request\n"
    "        return urllib.request.urlopen(url).read()\n"
    "    def format_output(self, data):\n"
    "        return str(data).strip()\n"
)

SRP_VIOLATION_WITH_METRIC = [
    {"principle": "SRP", "metric_id": "SRP-1", "issue": "Multiple responsibilities", "fix": "Extract concerns"}
]

HC = "code_health_check._check"
FM = "validate_swift_frontmatter.fix"

event = test_utils.event


def call_main(stdin_input) -> tuple:
    return test_utils.call_main(stdin_input, gate.main)
