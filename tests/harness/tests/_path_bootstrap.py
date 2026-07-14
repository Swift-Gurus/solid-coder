"""
solid-name: _path_bootstrap
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Configures the test execution environment to enable proper test imports.
"""

import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_HOOKS_TESTS = _PROJECT_ROOT / "mcp-server" / "hooks" / "tests"

_spec = importlib.util.spec_from_file_location(
    "_hooks_path_bootstrap", _HOOKS_TESTS / "_path_bootstrap.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

ensure_on_path = _mod.ensure_on_path

# Also add harness dir and all module subdirs (mirrors hooks/tests/_path_bootstrap)
_HARNESS_DIR = _PROJECT_ROOT / "tests" / "harness"
_MCP_HEALTH = _PROJECT_ROOT / "mcp-server" / "health"
for _d in (_HARNESS_DIR, _MCP_HEALTH, _MCP_HEALTH / "config", _MCP_HEALTH / "llm", _MCP_HEALTH / "codex"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))
