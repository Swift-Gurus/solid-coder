"""
solid-description: Provides test fixtures and utilities for validating frontmatter blocks.
solid-category: unit-test
"""

import json
from unittest.mock import MagicMock

BAD_CONTENT = """\
/**
 solid-name: DataLoader
 solid-category: service
 solid-description: Loads data using URLSession.shared and calls MyStorageManager.
 */
final class DataLoader {
    func load() {}
}
"""

CLEAN_CONTENT = """\
/**
 solid-name: DataLoader
 solid-category: service
 solid-description: Fetches remote data asynchronously and persists results to local storage.
 */
final class DataLoader {
    func load() {}
}
"""

BAD_PY_CONTENT = '''
"""
solid-name: loader
solid-category: service
solid-description: Loads data using requests.Session() and calls StorageManager.save().
"""

def load():
    pass
'''

CLEAN_PY_CONTENT = '''
"""
solid-name: loader
solid-category: service
solid-description: Fetches remote data and persists results to local storage.
"""

def load():
    pass
'''


def llm_raw(content: str) -> str:
    """Simulate the raw string returned by the LLM runner — a JSON object."""
    return json.dumps({"corrected_content": content})


def mock_runner(return_value):
    """Return a mock runner whose .run() returns return_value."""
    runner = MagicMock()
    runner.run.return_value = return_value
    return runner
