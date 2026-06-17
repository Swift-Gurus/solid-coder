"""
solid-description: Facade that registers managed LLM sessions and validates stop events.
solid-category: service
solid-tags: [hook, utility]
"""

import sys
from pathlib import Path
from typing import Optional, Protocol

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))


class SessionRegistering(Protocol):
    def register(self, session_id: str, session_type: str, cwd: str) -> dict: ...


class SessionValidating(Protocol):
    def validate(self, session_id: str, transcript_path: Optional[str], cwd: str) -> dict: ...


class SessionRegistry:
    """Facade: coordinates registration and stop-validation via protocol-typed subsystems."""

    def __init__(self, registrar: SessionRegistering, validator: SessionValidating) -> None:
        self._registrar = registrar
        self._validator = validator

    def register(self, session_id: str, session_type: str, cwd: str) -> dict:
        return self._registrar.register(session_id, session_type, cwd)

    def validate_stop(self, session_id: str, transcript_path: Optional[str], cwd: str) -> dict:
        return self._validator.validate(session_id, transcript_path, cwd)


def _make_registry() -> SessionRegistry:
    from mcp_tool_call_reader import make_mcp_tool_call_reader
    from session_registrar import SessionRegistrar
    from session_registry_accessor import SessionRegistryAccessor
    from session_stop_validator import SessionStopValidator
    from session_store import SessionStore
    from tool_call_checker import ToolCallChecker
    store = SessionStore()
    return SessionRegistry(
        registrar=SessionRegistrar(store=store),
        validator=SessionStopValidator(
            registry=SessionRegistryAccessor(store=store),
            checker=ToolCallChecker(reader=make_mcp_tool_call_reader()),
        ),
    )


def register_session(session_id: str, session_type: str, cwd: str) -> dict:
    """Gateway-callable: register a new managed session."""
    return _make_registry().register(session_id, session_type, cwd)


def validate_session_stop(session_id: str, transcript_path: Optional[str], cwd: str) -> dict:
    """Gateway-callable: validate a session stop."""
    return _make_registry().validate_stop(session_id, transcript_path, cwd)
