"""Verifies SessionStart captures typed project context."""

import io
import json
import sys
import unittest
from pathlib import Path


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_MCP_SERVER_DIRECTORY = _REPOSITORY_ROOT / "mcp-server"
if str(_MCP_SERVER_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(_MCP_SERVER_DIRECTORY))

from harness.json_loading import JsonLoader  # noqa: E402
from harness.pydantic_model_decoder import PydanticModelDecoder  # noqa: E402
from session.agent_start import (  # noqa: E402
    AgentStartApplication,
    AgentStartEvent,
    AgentStartEventParser,
    AgentStartHandler,
)


class StubCurrentDirectoryReader:
    def read(self) -> str:
        return "/fallback"


class StubEnvironmentReader:
    def __init__(self, session_type: str) -> None:
        self._session_type = session_type

    def get(self, key: str, default: str = "") -> str:
        return self._session_type


class RecordingSpy:
    def __init__(self) -> None:
        self.recorded: list[tuple[str, Path]] = []

    def record(self, session_id: str, project_directory: Path) -> None:
        self.recorded.append((session_id, project_directory))


class RegistrationSpy:
    def __init__(self) -> None:
        self.registered: list[tuple[str, str, str]] = []

    def register(self, session_id: str, session_type: str, cwd: str) -> dict:
        self.registered.append((session_id, session_type, cwd))
        return {"registered": True}


"""
solid-name: TestOnAgentStart
solid-category: unit-test
solid-description: Proves agent-start parsing and typed session registration behavior.
"""
class TestOnAgentStart(unittest.TestCase):

    def test_records_project_context_without_managed_session_type(self) -> None:
        recorder = RecordingSpy()
        registrar = RegistrationSpy()

        self._application(
            json.dumps({"session_id": "session-1", "cwd": "/project"}),
            "",
            recorder,
            registrar,
        ).run()

        self.assertEqual(recorder.recorded, [("session-1", Path("/project"))])
        self.assertEqual(registrar.registered, [])

    def test_preserves_managed_session_registration(self) -> None:
        recorder = RecordingSpy()
        registrar = RegistrationSpy()

        self._application(
            json.dumps({"session_id": "session-2", "cwd": "/project"}),
            "health_check",
            recorder,
            registrar,
        ).run()

        self.assertEqual(
            registrar.registered,
            [("session-2", "health_check", "/project")],
        )

    def test_uses_current_directory_when_payload_omits_cwd(self) -> None:
        recorder = RecordingSpy()

        self._application(
            json.dumps({"session_id": "session-3"}),
            "",
            recorder,
            RegistrationSpy(),
        ).run()

        self.assertEqual(recorder.recorded, [("session-3", Path("/fallback"))])

    def test_ignores_malformed_or_unidentified_events(self) -> None:
        recorder = RecordingSpy()
        registrar = RegistrationSpy()

        self._application("not-json", "health_check", recorder, registrar).run()
        self._application("{}", "health_check", recorder, registrar).run()

        self.assertEqual(recorder.recorded, [])
        self.assertEqual(registrar.registered, [])

    @staticmethod
    def _application(
        raw: str,
        session_type: str,
        recorder: RecordingSpy,
        registrar: RegistrationSpy,
    ) -> AgentStartApplication:
        return AgentStartApplication(
            input_reader=io.StringIO(raw),
            current_directory=StubCurrentDirectoryReader(),
            environment=StubEnvironmentReader(session_type),
            event_parser=AgentStartEventParser(
                json_loader=JsonLoader(),
                event_decoder=PydanticModelDecoder(AgentStartEvent),
            ),
            handler=AgentStartHandler(
                project_directory_recorder=recorder,
                session_registrar=registrar,
            ),
        )


if __name__ == "__main__":
    unittest.main()
