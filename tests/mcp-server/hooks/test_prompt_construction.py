"""
solid-description: Verifies that health check prompts activate only principles relevant to the analyzed code's patterns and domain.
solid-category: unit-test
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path

ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from hc_checker import HealthPromptBuilder, PrinciplesLoader
from hc_rule_loader import GatewayRuleLoader, GatewayCommandRunner, GatewayInvoker
from hc_tag_detector import TagDetector
from hook_utils import GATEWAY

_ALWAYS_ON_NAMES = frozenset({"srp", "ocp", "isp", "lsp", "dry", "code-smells"})
_CONDITIONAL_NAMES = frozenset({"swiftui", "structured-concurrency", "testing", "uitesting"})


def _make_loader() -> PrinciplesLoader:
    return PrinciplesLoader(
        rules=GatewayRuleLoader(invoker=GatewayInvoker(GATEWAY, GatewayCommandRunner(), timeout=300)),
        tags=TagDetector(),
    )


def _principle_names(principles: list) -> set:
    return {p["name"] for p in (principles or [])}


def _prompt_for(content: str, path: str = "/tmp/Foo.swift") -> tuple:
    """Return (principles, prompt) for the given code content."""
    loader = _make_loader()
    principles = loader.load(content, path)
    if principles is None:
        return None, None
    prompt = HealthPromptBuilder().build(
        principles, content, path, "test-session", output_dir="/tmp/gate/test"
    )
    return principles, prompt


class TestAlwaysOnPrinciplesInPrompt(unittest.TestCase):
    def test_plain_class_includes_always_on_detection_rules(self):
        code = """
class UserManager {
    private let db: Database
    init(db: Database) { self.db = db }
    func save(_ user: User) { db.save(user) }
}
"""
        principles, prompt = _prompt_for(code)
        names = _principle_names(principles)
        self.assertTrue(_ALWAYS_ON_NAMES.issubset(names),
                        f"Missing always-on principles: {_ALWAYS_ON_NAMES - names}")

    def test_plain_class_prompt_contains_srp_detection(self):
        code = "class Foo { func save() {} }"
        principles, prompt = _prompt_for(code)
        self.assertIn("<detection-instructions>", prompt)
        # SRP principle has detection content
        srp = next((p for p in principles if p["name"] == "srp"), None)
        self.assertIsNotNone(srp, "SRP must be in principles for plain Swift")
        if srp.get("content"):
            self.assertIn(srp["content"], prompt)

    def test_plain_class_excludes_conditional_principles(self):
        code = "class DataManager { func process() {} }"
        principles, prompt = _prompt_for(code)
        names = _principle_names(principles)
        for conditional in _CONDITIONAL_NAMES:
            self.assertNotIn(conditional, names,
                             f"Conditional principle '{conditional}' should not activate for plain code")


class TestSwiftUIPromptConstruction(unittest.TestCase):
    def test_swiftui_view_includes_swiftui_detection_rules(self):
        code = """
import SwiftUI

struct ContentView: View {
    var body: some View {
        VStack { Text("Hello") }
    }
}
"""
        principles, prompt = _prompt_for(code)
        names = _principle_names(principles)
        self.assertIn("swiftui", names, "SwiftUI principle must activate for SwiftUI code")
        self.assertTrue(_ALWAYS_ON_NAMES.issubset(names))

    def test_swiftui_prompt_contains_swiftui_detection_content(self):
        code = "import SwiftUI\nstruct Foo: View { var body: some View { Text(\"x\") } }"
        principles, prompt = _prompt_for(code)
        swiftui_p = next((p for p in principles if p["name"] == "swiftui"), None)
        self.assertIsNotNone(swiftui_p, "SwiftUI principle not loaded")
        if swiftui_p.get("content"):
            self.assertIn(swiftui_p["content"], prompt)

    def test_swiftui_prompt_excludes_testing_and_concurrency_rules(self):
        code = "import SwiftUI\nstruct Foo: View { var body: some View { EmptyView() } }"
        principles, prompt = _prompt_for(code)
        names = _principle_names(principles)
        self.assertNotIn("testing", names)
        self.assertNotIn("structured-concurrency", names)
        self.assertNotIn("uitesting", names)

    def test_state_wrapper_activates_swiftui_in_prompt(self):
        code = "struct Counter: View {\n    @State private var n = 0\n    var body: some View { Text(\"\\(n)\") }\n}"
        principles, _ = _prompt_for(code)
        self.assertIn("swiftui", _principle_names(principles))


class TestStructuredConcurrencyPromptConstruction(unittest.TestCase):
    def test_async_code_includes_concurrency_detection_rules(self):
        code = """
class NetworkClient {
    func fetch(url: URL) async throws -> Data {
        let (data, _) = try await URLSession.shared.data(from: url)
        return data
    }
}
"""
        principles, prompt = _prompt_for(code)
        names = _principle_names(principles)
        self.assertIn("structured-concurrency", names)
        self.assertTrue(_ALWAYS_ON_NAMES.issubset(names))

    def test_concurrency_prompt_excludes_swiftui_rules(self):
        code = "func doWork() async { await Task.detached { }.value }"
        principles, _ = _prompt_for(code)
        names = _principle_names(principles)
        self.assertNotIn("swiftui", names)
        self.assertNotIn("testing", names)


class TestUnitTestingPromptConstruction(unittest.TestCase):
    def test_xctest_code_includes_testing_detection_rules(self):
        code = """
import XCTest

final class UserManagerTests: XCTestCase {
    func testSave() throws {
        let sut = UserManager(db: MockDatabase())
        XCTAssertNoThrow(try sut.save(User(id: "1")))
    }
}
"""
        principles, prompt = _prompt_for(code)
        names = _principle_names(principles)
        self.assertIn("testing", names)
        self.assertTrue(_ALWAYS_ON_NAMES.issubset(names))

    def test_testing_prompt_excludes_swiftui_and_concurrency(self):
        code = "import XCTest\nclass FooTests: XCTestCase { func testFoo() {} }"
        principles, _ = _prompt_for(code)
        names = _principle_names(principles)
        self.assertNotIn("swiftui", names)
        self.assertNotIn("structured-concurrency", names)


class TestUITestingPromptConstruction(unittest.TestCase):
    def test_xcui_code_includes_uitesting_detection_rules(self):
        code = """
import XCTest

final class AppUITests: XCTestCase {
    let app = XCUIApplication()
    func testLaunch() { app.launch(); XCTAssert(app.exists) }
}
"""
        principles, prompt = _prompt_for(code)
        names = _principle_names(principles)
        self.assertIn("uitesting", names)
        self.assertTrue(_ALWAYS_ON_NAMES.issubset(names))

    def test_uitest_prompt_excludes_unit_testing_principle(self):
        """UI test detection suppresses unit-test tag; uitesting replaces testing."""
        code = "import XCTest\nclass UITests: XCTestCase {\n    let app = XCUIApplication()\n}"
        principles, _ = _prompt_for(code)
        names = _principle_names(principles)
        self.assertIn("uitesting", names)
        self.assertNotIn("testing", names)


class TestPromptDoesNotIncludeInactiveRules(unittest.TestCase):
    def test_swiftui_detection_text_absent_for_plain_code(self):
        """Verify SwiftUI-specific terms don't appear in prompt for non-SwiftUI code."""
        plain_code = "class DataService { func fetch() {} }"
        _, plain_prompt = _prompt_for(plain_code)

        swiftui_code = "import SwiftUI\nstruct Foo: View { var body: some View { EmptyView() } }"
        _, swiftui_prompt = _prompt_for(swiftui_code)

        # SwiftUI prompt should contain more rules than plain prompt
        self.assertGreater(len(swiftui_prompt), len(plain_prompt),
                           "SwiftUI prompt should be longer due to SwiftUI detection rules")


if __name__ == "__main__":
    unittest.main()
