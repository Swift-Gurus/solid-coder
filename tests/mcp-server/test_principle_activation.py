"""solid-description: Tests that code pattern detection activates the correct set of review principles.

Pipeline under test:
  TagDetector.detect(content, candidate_tags) → matched_tags
  load_detection_rules(matched_tags) → principles

solid-category: unit-test
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

_MCP_DIR = Path(__file__).resolve().parents[2] / "mcp-server"
_HOOKS_DIR = _MCP_DIR.parent / "hooks"
sys.path.insert(0, str(_MCP_DIR))
sys.path.insert(0, str(_HOOKS_DIR))
import sys as _sys
from pathlib import Path as _Path
_PROJECT_ROOT = _Path(__file__).resolve().parents[2]
_sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server/health"))

from hc_tag_detector import TagDetector
from helpers import SubmitFindingsTestBase

_GATEWAY = str(Path(__file__).resolve().parents[2] / "mcp-server" / "gateway.py")

_ALWAYS_ON = frozenset({"srp", "ocp", "isp", "lsp", "dry", "code-smells", "frontmatter"})


def _candidate_tags() -> list:
    result = subprocess.run(
        [sys.executable, _GATEWAY, "get_candidate_tags"],
        capture_output=True, text=True,
    )
    return json.loads(result.stdout)["candidate_tags"]


class PrincipleActivationTester:
    """Runs the tag-detection → principle-loading pipeline against the gateway CLI."""

    def __init__(self, gateway_path: str, tag_detector: TagDetector) -> None:
        self._gateway_path = gateway_path
        self._tag_detector = tag_detector

    def detect_tags(self, content: str) -> list:
        return self._tag_detector.detect(content, _candidate_tags())

    def load_principles(self, tags: list) -> set:
        # Always passes --matched_tags (even when empty) so that:
        # - No tags detected → only always-on principles (empty matched_tags filters out conditional)
        # - Tags detected → always-on + matching conditional principles
        result = subprocess.run(
            [sys.executable, self._gateway_path, "load_detection_rules",
             "--matched_tags", ",".join(tags)],
            capture_output=True, text=True,
        )
        return {p["name"] for p in json.loads(result.stdout)["principles"]}

    def principles_for_code(self, content: str) -> set:
        return self.load_principles(self.detect_tags(content))


class TestAlwaysOnPrinciples(unittest.TestCase):
    def setUp(self):
        self.tester = PrincipleActivationTester(_GATEWAY, TagDetector())

    def test_plain_swift_class_activates_only_always_on(self):
        code = """
class UserManager {
    private let database: Database
    init(database: Database) { self.database = database }
    func save(_ user: User) { database.save(user) }
}
"""
        names = self.tester.principles_for_code(code)
        self.assertEqual(names, _ALWAYS_ON)

    def test_empty_file_activates_only_always_on(self):
        names = self.tester.principles_for_code("")
        # Empty matched_tags → always-on only (no conditional principles match)
        self.assertTrue(_ALWAYS_ON.issubset(names))
        self.assertNotIn("swiftui", names)
        self.assertNotIn("testing", names)


class TestSwiftUIActivation(unittest.TestCase):
    def setUp(self):
        self.tester = PrincipleActivationTester(_GATEWAY, TagDetector())

    def test_import_swiftui_activates_swiftui(self):
        code = "import SwiftUI\n\nstruct MyView: View {\n    var body: some View { Text(\"hi\") }\n}"
        names = self.tester.principles_for_code(code)
        self.assertIn("swiftui", names)
        self.assertTrue(_ALWAYS_ON.issubset(names))

    def test_view_conformance_activates_swiftui(self):
        code = "struct ContentView: View {\n    var body: some View { EmptyView() }\n}"
        names = self.tester.principles_for_code(code)
        self.assertIn("swiftui", names)

    def test_state_property_wrapper_activates_swiftui(self):
        code = "struct Counter: View {\n    @State private var count = 0\n    var body: some View { Text(\"\\(count)\") }\n}"
        names = self.tester.principles_for_code(code)
        self.assertIn("swiftui", names)

    def test_swiftui_does_not_activate_testing_or_concurrency(self):
        code = "import SwiftUI\nstruct MyView: View { var body: some View { EmptyView() } }"
        names = self.tester.principles_for_code(code)
        self.assertNotIn("testing", names)
        self.assertNotIn("uitesting", names)
        self.assertNotIn("structured-concurrency", names)


class TestStructuredConcurrencyActivation(unittest.TestCase):
    def setUp(self):
        self.tester = PrincipleActivationTester(_GATEWAY, TagDetector())

    def test_async_await_activates_structured_concurrency(self):
        code = """
class NetworkClient {
    func fetchUser(id: String) async throws -> User {
        let data = try await URLSession.shared.data(from: url)
        return try decoder.decode(User.self, from: data)
    }
}
"""
        names = self.tester.principles_for_code(code)
        self.assertIn("structured-concurrency", names)
        self.assertTrue(_ALWAYS_ON.issubset(names))

    def test_task_block_activates_structured_concurrency(self):
        code = "func start() { Task { await doWork() } }"
        names = self.tester.principles_for_code(code)
        self.assertIn("structured-concurrency", names)

    def test_actor_declaration_activates_structured_concurrency(self):
        code = "actor DataCache {\n    private var store: [String: Data] = [:]\n}"
        names = self.tester.principles_for_code(code)
        self.assertIn("structured-concurrency", names)

    def test_concurrency_does_not_activate_swiftui_or_testing(self):
        code = "func fetch() async -> Data { await download() }"
        names = self.tester.principles_for_code(code)
        self.assertNotIn("swiftui", names)
        self.assertNotIn("testing", names)


class TestUnitTestingActivation(unittest.TestCase):
    def setUp(self):
        self.tester = PrincipleActivationTester(_GATEWAY, TagDetector())

    def test_xctest_import_activates_testing(self):
        code = "import XCTest\n\nfinal class UserTests: XCTestCase {\n    func testSave() { XCTAssert(true) }\n}"
        names = self.tester.principles_for_code(code)
        self.assertIn("testing", names)
        self.assertTrue(_ALWAYS_ON.issubset(names))

    def test_swift_testing_import_activates_testing(self):
        code = "import Testing\n\n@Suite struct UserTests {\n    @Test func save() {}\n}"
        names = self.tester.principles_for_code(code)
        self.assertIn("testing", names)

    def test_test_annotation_activates_testing(self):
        code = "@Test func verifyUserSave() throws { }"
        names = self.tester.principles_for_code(code)
        self.assertIn("testing", names)

    def test_unit_test_does_not_activate_swiftui_or_concurrency(self):
        code = "import XCTest\nclass Tests: XCTestCase { func testFoo() {} }"
        names = self.tester.principles_for_code(code)
        self.assertNotIn("swiftui", names)
        self.assertNotIn("structured-concurrency", names)


class TestUITestingActivation(unittest.TestCase):
    def setUp(self):
        self.tester = PrincipleActivationTester(_GATEWAY, TagDetector())

    def test_xcuiapplication_activates_uitesting(self):
        code = """
import XCTest

final class AppUITests: XCTestCase {
    let app = XCUIApplication()
    func testLaunch() { app.launch() }
}
"""
        names = self.tester.principles_for_code(code)
        self.assertIn("uitesting", names)
        self.assertTrue(_ALWAYS_ON.issubset(names))

    def test_xcuielement_activates_uitesting(self):
        code = "let button: XCUIElement = app.buttons[\"Submit\"]"
        names = self.tester.principles_for_code(code)
        self.assertIn("uitesting", names)

    def test_ui_test_excludes_unit_testing_and_xctest(self):
        """XCUIApplication suppresses unit-test and xctest tags — ui-test takes precedence."""
        code = "import XCTest\nfinal class UITests: XCTestCase {\n    let app = XCUIApplication()\n}"
        names = self.tester.principles_for_code(code)
        self.assertIn("uitesting", names)
        # unit-test and xctest are suppressed when ui-test is detected
        self.assertNotIn("testing", names)


if __name__ == "__main__":
    unittest.main()
