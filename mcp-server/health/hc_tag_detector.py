"""
solid-description: Detects which candidate principle tags are active in a given source file.
solid-category: service
solid-tags: [hook, detection]
"""

import sys
from pathlib import Path
_HEALTH_DIR = Path(__file__).resolve().parent
_HOOKS_DIR = _HEALTH_DIR.parents[1] / 'hooks'
for _d in (_HOOKS_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import re
from typing import Protocol


class TagDetecting(Protocol):
    def detect(self, content: str, candidate_tags: list) -> list: ...


class TagDetector:
    """Identifies active principle tags by scanning content for import and usage patterns."""

    _PATTERNS: dict = {
        "swiftui": [
            r"\bimport\s+SwiftUI\b",
            r":\s*View\b",           # conforming to View protocol
            r"\bsome\s+View\b",      # returning some View
            r"\b@State\b",
            r"\b@StateObject\b",
            r"\b@ObservedObject\b",
            r"\b@Observable\b",
        ],
        "structured-concurrency": [
            r"\basync\b",
            r"\bawait\b",
            r"\bTask\s*[{<(.]",      # Task { }, Task<T>, Task(, Task.detached — not URLSessionTask
            r"\bactor\s+\w",         # actor keyword declaration, not Actor type
        ],
        "unit-test": [r"\bimport\s+Testing\b", r"\bXCTestCase\b", r"@Test\b"],
        "ui-test": [r"\bXCUIApplication\b", r"\bXCUIElement\b"],
        "xctest": [r"\bimport\s+XCTest\b"],
    }

    def detect(self, content: str, candidate_tags: list) -> list:
        matched = [
            tag for tag in candidate_tags
            if any(re.search(p, content) for p in self._PATTERNS.get(tag, []))
        ]
        if "ui-test" in matched:
            return [t for t in matched if t not in ("unit-test", "xctest")]
        return [t for t in matched if t != "ui-test"]
