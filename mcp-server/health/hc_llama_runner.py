"""
solid-description: Coordinates code analysis with violation detection.
solid-category: service
solid-tags: [hook, llm]
"""

import sys
from pathlib import Path
from typing import Optional

_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (_MCP_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hook_utils import PLUGIN_ROOT as _PR  # resolve PLUGIN_ROOT early for path setup  # noqa: E402
_MCP_SERVER_DIR = str(_PR / "mcp-server")
if _MCP_SERVER_DIR not in sys.path:
    sys.path.insert(0, _MCP_SERVER_DIR)

from hook_utils import GATEWAY, PLUGIN_ROOT, solid_coder_project_dir  # noqa: E402
import hc_config  # noqa: E402
from hc_rule_loader import GatewayCommandRunner, GatewayInvoker, GatewayFixInvoker  # noqa: E402
from hc_violation_parser import ViolationParser, ViolationParsing  # noqa: E402
from health.dry_search_service_factory import DrySearchServiceFactory  # noqa: E402

from llama.urllib_opener import HttpOpening, UrllibOpener  # noqa: E402, F401
from llama.urllib_request_builder import HttpRequestBuilding, UrllibRequestBuilder  # noqa: E402, F401
from llama.urllib_sender import HttpSending, UrllibSender  # noqa: E402, F401
from llama.json_serializer import JsonSerializing, JsonSerializer  # noqa: E402, F401
from llama.json_deserializer import JsonDeserializing, JsonDeserializer  # noqa: E402, F401
from llama.http_client import LlamaHttpChatting, LlamaHttpClient  # noqa: E402, F401
from llama.log_entry_writer import LogEntryWriting, JsonlEntryWriter  # noqa: E402, F401
from llama.timer import TimeMeasuring, MonotonicTimer  # noqa: E402, F401
from llama.directory_creator import DirectoryCreating, PathDirectoryCreator  # noqa: E402, F401
from llama.logger import LocalLLMLogger  # noqa: E402, F401
from llama.session_observer import LLMSessionObserving, LLMSessionObserver  # noqa: E402, F401
from llama.findings_submitter import BatchFindingsHandling, FindingsSubmitting, GatewayFindingsSubmitter  # noqa: E402, F401
from llama.tool_call_parser import ToolCallArgsParsing, ToolCallParser  # noqa: E402, F401
from llama.codebase_searcher import CodebaseSearcher  # noqa: E402, F401
from llama.tool_dispatcher import ToolDispatching, GatewayToolDispatcher, TOOLS  # noqa: E402, F401
from llama.builtin_range import RangeIterating, BuiltinRange  # noqa: E402, F401
from llama.thinking_extractor import ThinkingExtracting, ThinkingExtractor  # noqa: E402, F401
from llama.tool_call_orchestrating import ToolCallOrchestrating  # noqa: E402, F401
from llama.tool_call_orchestrator import ToolCallOrchestrator  # noqa: E402, F401
from llama.agent_loop import AgentLoopExecuting, AgentLoopExecutor  # noqa: E402, F401

# Backward-compatible aliases for test imports
_te = ThinkingExtractor()
_strip_thinking = _te.strip
_extract_thinking_and_content = _te.extract

_MAX_TOOL_ROUNDS = 10


"""
solid-name: LlamaServerRunner
solid-category: service
solid-description: Runs the local health-check agent lifecycle and reports its observed result.
"""
class LlamaServerRunner:
    """Coordinates review lifecycle: start → loop → parse violations → done."""

    def __init__(
        self,
        loop: AgentLoopExecuting,
        observer: Optional[LLMSessionObserving] = None,
        parser: Optional[ViolationParsing] = None,
    ) -> None:
        self._loop = loop
        self._observer = observer
        self._parser = parser

    def run(self, prompt: str, timeout: int) -> Optional[str]:
        if self._observer:
            self._observer.on_start(len(prompt))
        messages: list = [{"role": "user", "content": prompt}]
        content, usage, rounds, thinking = self._loop.execute(messages, timeout, self._observer)
        if self._observer:
            violations = (self._parser.parse(content) or []) if self._parser and content else []
            self._observer.on_done(rounds, usage, violations, thinking=thinking)
        return content


def make_llama_server_runner(
    host: str,
    model: str,
    gateway: Path = GATEWAY,
    session_id: str = "",
    file_path: str = "",
) -> LlamaServerRunner:
    """Wire production defaults and return a ready-to-use LlamaServerRunner.

    Factory function — constructing and wiring concrete dependencies is this
    function's sole responsibility (OCP Factory exception).
    """
    invoker = GatewayInvoker(gateway, GatewayCommandRunner(), timeout=hc_config.load_config().llm.timeout)
    observer: Optional[LLMSessionObserving] = None
    if session_id:
        log_dir = solid_coder_project_dir() / "llm-sessions" / session_id
        logger = LocalLLMLogger(log_dir=log_dir, file_path=file_path, model=model)
        observer = LLMSessionObserver(logger=logger)

    from lib.gateway_tools import make_gateway_handler  # noqa: PLC0415
    from search.file_searcher import grep_by_name, glob_by_name  # noqa: PLC0415
    from search import codebase_searcher  # noqa: PLC0415

    gw_handler = make_gateway_handler(PLUGIN_ROOT / "references")
    dry_search_services = DrySearchServiceFactory()
    dry_search = dry_search_services.make_search(codebase_searcher)
    guarded_submission = dry_search_services.make_submission(gw_handler)
    findings_submitter = GatewayFindingsSubmitter(handler=guarded_submission)
    arg_parser = ToolCallParser()
    searcher = CodebaseSearcher(
        search_fn=lambda query, output_dir: dry_search.search(
            query=query,
            output_dir=output_dir,
            min_matches=1,
        ),
        grep_fn=grep_by_name,
        glob_fn=glob_by_name,
        read_fn=lambda p: Path(p).read_text(encoding="utf-8"),
    )
    dispatcher = GatewayToolDispatcher(
        codebase_search=searcher,
        fix_invoker=GatewayFixInvoker(invoker=invoker),
        parser=arg_parser,
        findings_submitter=findings_submitter,
    )
    orchestrator = ToolCallOrchestrator(dispatcher=dispatcher, arg_parser=arg_parser)
    thinker = ThinkingExtractor()
    loop = AgentLoopExecutor(
        client=LlamaHttpClient(host=host, model=model, inference_params=hc_config.load_config().inference.model_dump()),
        orchestrator=orchestrator,
        thinker=thinker,
        max_rounds=_MAX_TOOL_ROUNDS,
    )
    return LlamaServerRunner(loop=loop, observer=observer, parser=ViolationParser())
