"""
solid-name: RunPrincipleTestsCLI
solid-category: utility
solid-spec: [SPEC-014]
solid-description: Runs principle integration tests with configurable principle and flow parameters.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_HARNESS_DIR = _TESTS_DIR / "harness"
_PROJECT_ROOT = _TESTS_DIR.parent
_MCP_SERVER = _PROJECT_ROOT / "mcp-server"
_MCP_HEALTH = _MCP_SERVER / "health"
for _d in (
    str(_HARNESS_DIR),
    str(_TESTS_DIR),
    str(_MCP_SERVER),
    str(_MCP_SERVER / "utils"),
    str(_MCP_SERVER / "output"),
    str(_MCP_SERVER / "gate"),
    str(_MCP_SERVER / "patch"),
    str(_MCP_SERVER / "session"),
    str(_MCP_HEALTH),
    str(_MCP_HEALTH / "config"),
    str(_MCP_HEALTH / "llm"),
    str(_MCP_HEALTH / "codex"),
):
    if _d not in sys.path:
        sys.path.insert(0, _d)

from harness_factory import HarnessFactory  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run principle integration tests.")
    parser.add_argument("--principle", required=True, help="references/ path to the principle")
    parser.add_argument("--flow", choices=["apply", "health"], help="flow to run (default: both)")
    parser.add_argument("--fixture", help="single fixture stem to run")
    parser.add_argument("--model", help="model profile name (tests/models/<name>.toml)")
    parser.add_argument("--mode", choices=["direct", "e2e"], default="direct")
    parser.add_argument(
        "--timeout", type=int, default=None,
        help="per-fixture timeout in seconds (default: the model profile's own llm.timeout)",
    )
    args = parser.parse_args()

    if args.mode == "e2e":
        print("e2e mode not yet implemented", file=sys.stderr)
        sys.exit(1)

    principle_folder = _PROJECT_ROOT / args.principle
    factory = HarnessFactory()
    runner = factory.build(_PROJECT_ROOT, principle_folder)
    passed = runner.run(
        principle_path=args.principle,
        flow=args.flow,
        fixture_filter=args.fixture,
        model_name=args.model,
        timeout=args.timeout,
    )
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
