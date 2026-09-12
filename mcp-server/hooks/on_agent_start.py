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

from harness.json_loading import JsonLoader  # noqa: E402
from harness.os_env_reader import OsEnvReader  # noqa: E402
from harness.pydantic_model_decoder import PydanticModelDecoder  # noqa: E402
from session.agent_start import (  # noqa: E402
    AgentStartApplication,
    AgentStartEvent,
    AgentStartEventParser,
    AgentStartHandler,
    ProcessCurrentDirectoryReader,
    StdinAgentStartInputReader,
)
from session.project_context import (  # noqa: E402
    SessionProjectContextPathResolver,
    SessionProjectDirectoryRecorder,
)
from session.session_registrar import SessionRegistrar  # noqa: E402
from session.session_store import SessionStore  # noqa: E402


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
                SessionProjectContextPathResolver()
            ),
            session_registrar=SessionRegistrar(SessionStore()),
        ),
    ).run()


if __name__ == "__main__":
    main()
