"""
solid-name: ConcurrentHandlerExecutor
solid-category: service
solid-description: Executes applicable handlers concurrently and returns their decisions.
solid-tags: [hook]
"""

from typing import List

from handler_executing import HandlerExecuting
from handler_pool_running import HandlerPoolRunning
from hook_decision import HookDecision
from hook_handling import HookHandling
from safe_handler_running import SafeHandlerRunning
from safe_handler_runner import SafeHandlerRunner
from thread_pool_handler_runner import ThreadPoolHandlerRunner


class ConcurrentHandlerExecutor(HandlerExecuting):
    def __init__(
        self,
        handlers: List[HookHandling],
        safe_runner: SafeHandlerRunning = SafeHandlerRunner(),
        pool_runner: HandlerPoolRunning = ThreadPoolHandlerRunner(),
    ) -> None:
        self._handlers = handlers
        self._safe_runner = safe_runner
        self._pool_runner = pool_runner

    def run(self, event: dict) -> List[HookDecision]:
        applicable = [h for h in self._handlers if h.should_handle(event)]
        return self._pool_runner.map(lambda handler: self._safe_runner.run(handler, event), applicable)