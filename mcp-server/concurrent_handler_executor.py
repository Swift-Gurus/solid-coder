"""
solid-name: ConcurrentHandlerExecutor
solid-category: service
solid-description: Executes applicable handlers concurrently and returns their decisions.
solid-tags: [hook]
"""

from handler_executing import HandlerExecuting
from handler_pool_running import HandlerPoolRunning
from hook_decision import HookDecision
from hook_handling import HookHandling
from safe_handler_runner import SafeHandlerRunner
from safe_handler_running import SafeHandlerRunning
from thread_pool_handler_runner import ThreadPoolHandlerRunner

_DEFAULT_SAFE_RUNNER: SafeHandlerRunning = SafeHandlerRunner()
_DEFAULT_POOL_RUNNER: HandlerPoolRunning = ThreadPoolHandlerRunner()


class ConcurrentHandlerExecutor(HandlerExecuting):
    def __init__(
        self,
        handlers: list[HookHandling],
        safe_runner: SafeHandlerRunning = _DEFAULT_SAFE_RUNNER,
        pool_runner: HandlerPoolRunning = _DEFAULT_POOL_RUNNER,
    ) -> None:
        self._handlers = handlers
        self._safe_runner = safe_runner
        self._pool_runner = pool_runner

    def run(self, event: dict) -> list[HookDecision]:
        applicable = [h for h in self._handlers if h.should_handle(event)]
        return self._pool_runner.map(
            lambda handler: self._safe_runner.run(handler, event), applicable
        )
