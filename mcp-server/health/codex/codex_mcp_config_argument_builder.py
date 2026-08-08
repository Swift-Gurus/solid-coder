"""Translates health MCP configuration into Codex CLI overrides."""

from codex_config_argument_building import CodexConfigArgumentBuilding
from llama.json_deserializer import JsonDeserializing
from llama.json_serializer import JsonSerializing


"""
solid-name: CodexMcpConfigArgumentBuilder
solid-category: adapter
solid-description: Translates session server configuration into command-line override arguments.
solid-tags: [hook, llm]
"""
class CodexMcpConfigArgumentBuilder(CodexConfigArgumentBuilding):
    def __init__(
        self,
        deserializer: JsonDeserializing,
        serializer: JsonSerializing,
    ) -> None:
        self._deserializer = deserializer
        self._serializer = serializer

    def build(self, mcp_config: str) -> list[str]:
        if not mcp_config.strip():
            return []
        configuration = self._deserializer.deserialize(mcp_config.encode("utf-8")) or {}
        arguments: list[str] = []
        for name, server in configuration.get("mcpServers", {}).items():
            prefix = f"mcp_servers.{name}"
            command = self._serializer.serialize(server["command"])
            server_arguments = self._serializer.serialize(server.get("args", []))
            arguments.extend(["-c", f"{prefix}.command={command}"])
            arguments.extend(["-c", f"{prefix}.args={server_arguments}"])
        return arguments
