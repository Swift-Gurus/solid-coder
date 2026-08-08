"""
solid-description: Guards against hooks.json's static per-hook timeout entries drifting from each other.
solid-category: unit-test
"""

import json
import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from hook_utils import PLUGIN_ROOT  # noqa: E402


def _iter_hook_entries(hooks_json: dict):
    for entries in hooks_json.get("hooks", {}).values():
        for entry in entries:
            for hook in entry.get("hooks", []):
                yield hook


class TestHooksJsonTimeout(unittest.TestCase):
    """hooks.json can't read config.toml at hook-invocation time (static file, confirmed via
    code.claude.com/docs/en/hooks — hook timeouts are file-based only, no CLI flag can set
    them at runtime) — this is the one spot the configured [llm].timeout can't reach, so every
    entry here is a manually-set literal. This test just keeps them all consistent with each
    other so one entry can't silently drift from the rest.
    """

    def test_every_hook_declares_the_same_timeout(self):
        hooks_json_path = PLUGIN_ROOT / "hooks" / "hooks.json"
        data = json.loads(hooks_json_path.read_text(encoding="utf-8"))
        hooks = list(_iter_hook_entries(data))
        self.assertTrue(hooks, "expected at least one hook entry in hooks.json")
        timeouts = {hook.get("command"): hook.get("timeout") for hook in hooks}
        distinct = set(timeouts.values())
        self.assertEqual(len(distinct), 1, f"hook timeouts have drifted apart: {timeouts}")
        self.assertNotIn(None, distinct, "every hook entry must declare an explicit timeout")


if __name__ == "__main__":
    unittest.main()
