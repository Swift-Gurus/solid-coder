"""Owns process streams and bounded RPC exchange for semantic providers."""

import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from content_length_reader import ContentLengthReader
from content_length_writer import ContentLengthWriter
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.thread_pool_executor_factory import ThreadPoolExecutorFactory
from health.llama.timer import MonotonicTimer
from source.analysis.provenance.bounded_rpc_message_reader import (
    BoundedRpcMessageReader,
)
from source.analysis.provenance.rpc_inbound_message import RpcInboundMessage
from source.analysis.provenance.stdio_rpc_channel import RpcExchanging, StdioRpcChannel

"""
solid-name: BoundedRpcProcessFactory
solid-category: factory
solid-spec: [SPEC-064]
solid-description: Creates bounded semantic subprocess channels and closes their streams on success, failure, or timeout.
"""


class BoundedRpcProcessFactory:
    def __init__(self, timeout_seconds: float = 30) -> None:
        self._timeout_seconds = timeout_seconds

    @contextmanager
    def open(
        self, command: list[str], project_root: Path, stderr_path: Path
    ) -> Iterator[RpcExchanging]:
        with stderr_path.open("w+b") as stderr:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=stderr,
                cwd=project_root,
            )
            with ThreadPoolExecutorFactory().create(max_workers=1) as executor:
                try:
                    if process.stdin is None or process.stdout is None:
                        raise ConnectionError(
                            "Semantic process streams are unavailable."
                        )
                    yield StdioRpcChannel(
                        outgoing=process.stdin,
                        reader=BoundedRpcMessageReader(
                            incoming=process.stdout,
                            reader=ContentLengthReader(),
                            decoder=PydanticModelDecoder(RpcInboundMessage),
                            executor=executor,
                        ),
                        writer=ContentLengthWriter(),
                        timer=MonotonicTimer(),
                        timeout_seconds=self._timeout_seconds,
                    )
                finally:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=5)
                    for stream in (process.stdin, process.stdout):
                        if stream is not None:
                            stream.close()
