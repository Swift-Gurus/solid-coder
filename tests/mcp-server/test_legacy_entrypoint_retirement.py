"""Checks disabled discovery stays reversible and cannot expose retired MCP handlers."""

import hashlib
import json
import re
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml
from handler_store import HandlerStore
from mcp_server_factory import MCPServerFactory
from tool_metadata_store import ToolMetadataStore
from tool_result_formatter import ToolResultFormatter
from tools_call_handler import ToolsCallHandler

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / ".claude/docs/legacy-entrypoint-retirement-2026-10-23.json"


@pytest.mark.parametrize(
    "enabled, expected",
    [
        (None, {"kept", "retired"}),
        (frozenset({"kept"}), {"kept"}),
        (frozenset(), set()),
    ],
)
def test_registration_policy_filters_metadata_and_invocation_but_keeps_direct_functions(
    enabled: frozenset[str] | None,
    expected: set[str],
) -> None:
    metadata, handlers = ToolMetadataStore(), HandlerStore()
    server = MCPServerFactory(metadata=metadata, handlers=handlers).build(
        "policy", enabled_tools=enabled
    )
    functions = {}
    schema, meta = {"type": "object"}, {"test": True}
    for name in ("kept", "retired"):
        function = Mock(return_value=42)
        decorated = server.tool(
            name=name, description=name, input_schema=schema, meta=meta
        )(function)
        assert decorated is function
        functions[name] = decorated

    assert {tool["name"] for tool in metadata.list_all()} == expected
    for tool in metadata.list_all():
        assert tool["inputSchema"] == schema
        assert tool["_meta"] == meta
    caller = ToolsCallHandler(handlers, ToolResultFormatter())
    for name, function in functions.items():
        if name not in expected:
            with pytest.raises(LookupError, match="Unknown tool"):
                caller.handle(name, {}, None)
            function.assert_not_called()
        else:
            assert caller.handle(name, {}, None)["content"]
            function.assert_called_once_with()
        # CLI/internal calls still work even when no MCP registration exists.
        assert function() == 42


def test_configured_servers_keep_flow_health_dependencies_and_apple_without_specs() -> (
    None
):
    checkout = json.loads((ROOT / ".mcp.json").read_text())["mcpServers"]
    claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())["mcpServers"]
    assert set(checkout) == {
        "solid-coder-apple-build",
        "solid-coder-docs",
        "solid-coder-flow-engine",
        "solid-coder-pipeline",
    }
    assert set(claude) == {"apple-build", "docs", "flow-engine", "pipeline"}
    assert checkout["solid-coder-flow-engine"]["args"] == [
        "mcp-server/flow_engine/server.py"
    ]
    assert claude["flow-engine"]["args"] == [
        "${CLAUDE_PLUGIN_ROOT}/mcp-server/flow_engine/server.py"
    ]
    ledger = json.loads(LEDGER.read_text())
    for removed in ledger["removed_server_registrations"].values():
        for entry in removed.values():
            assert entry["args"][0].endswith("mcp-server/specs/server.py")
    assert (ROOT / "mcp-server/specs/server.py").is_file()
    assert (ROOT / "skills/find-spec/scripts/find-spec-query.py").is_file()
    assert (ROOT / "skills/build-spec/scripts/build-spec-query.py").is_file()


def test_disabled_entrypoints_preserve_exact_copies_outside_discovery() -> None:
    ledger = json.loads(LEDGER.read_text())
    for entry in ledger["archived_entrypoints"]:
        assert not (ROOT / entry["original"]).exists()
        archived = ROOT / entry["disabled"]
        assert hashlib.sha256(archived.read_bytes()).hexdigest() == entry["sha256"]
    active_skills = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
    active_agents = {p.stem for p in (ROOT / "agents").glob("*.md")}
    assert active_skills == set(ledger["active_skills"])
    assert active_agents == set(ledger["active_agents"])
    for agent in (ROOT / "agents").glob("*.md"):
        frontmatter = yaml.safe_load(agent.read_text().split("---", 2)[1])
        assert set(frontmatter.get("skills", [])) <= active_skills
    # This project agent uses dedicated flow-engine, not the retired orchestration.
    assert (ROOT / ".claude/agents/review-test.md").is_file()


def test_retained_skill_and_agent_tool_dependencies_are_available() -> None:
    ledger = json.loads(LEDGER.read_text())
    namespace = {
        "docs": "docs",
        "pipeline": "pipeline",
        "flow-engine": "flow_engine",
        "apple-build": "build/apple",
    }
    entries = list((ROOT / "skills").glob("*/SKILL.md")) + list(
        (ROOT / "agents").glob("*.md")
    )
    pattern = r"mcp__plugin_solid-coder_(docs|pipeline|flow-engine|apple-build|specs)__([a-z_]+)"
    for entry in entries:
        for server, tool in re.findall(pattern, entry.read_text()):
            assert server in namespace, (entry, server)
            assert tool in ledger["active_mcp_tools"][namespace[server]], (entry, tool)


def test_health_session_allowed_tools_remain_registered() -> None:
    import ast

    ledger = json.loads(LEDGER.read_text())
    for relative in [
        "mcp-server/health/hc_checker_factory.py",
        "mcp-server/health/workflow_health_checker_factory.py",
        "tests/harness/apply_flow_invoker.py",
    ]:
        module = ast.parse((ROOT / relative).read_text())
        assignment = next(
            node
            for node in module.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "_ALLOWED_TOOLS"
                for target in node.targets
            )
        )
        for name in ast.literal_eval(assignment.value).split(","):
            if not name.startswith("mcp__"):
                continue
            namespace, tool = name.removeprefix("mcp__").split("__", 1)
            server = (
                "flow_engine" if namespace == "solid-coder-flow-engine" else namespace
            )
            assert tool in ledger["active_mcp_tools"][server], (relative, name)
