"""
solid-description: Registers session identity, type, and working directory from provided input.
solid-category: service
solid-tags: [hook]
"""

import sys
from pathlib import Path

_MCP_DIR = Path(__file__).resolve().parents[1]
for _d in (_MCP_DIR,):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from harness.json_loading import JsonLoader
from harness.os_env_reader import OsEnvReader
from harness.pydantic_model_decoder import PydanticModelDecoder
from session.agent_start import (
    AgentStartApplication,
    AgentStartEvent,
    AgentStartEventParser,
    AgentStartHandler,
    ProcessCurrentDirectoryReader,
    StdinAgentStartInputReader,
)
from session.project_context import (
    DEFAULT_SESSION_ROOT,
    SessionProjectContextPathResolver,
    SessionProjectDirectoryRecorder,
)
from session.session_registrar import SessionRegistrar
from session.session_store import SessionStore


def main() -> None:
    AgentStartApplication(
        input_reader=StdinAgentStartInputReader(),
        current_directory=ProcessCurrentDirectoryReader(),
        environment=OsEnvReader(),
        event_parser=AgentStartEventParser(
            json_loader=JsonLoader(),
            event_decoder=PydanticModelDecoder(AgentStartEvent),
        ),
        handler=AgentStartHandler(
            project_directory_recorder=SessionProjectDirectoryRecorder(
                SessionProjectContextPathResolver(root_directory=DEFAULT_SESSION_ROOT)
            ),
            session_registrar=SessionRegistrar(SessionStore()),
        ),
    ).run()


if __name__ == "__main__":
    main()
