"""Private entry point for isolated native semantic requests."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from harness.pydantic_model_decoder import PydanticModelDecoder
from json_rpc_response_builder import JsonRpcResponseBuilder
from raw_stdin_source import RawStdinSource
from raw_stdout_sink import RawStdoutSink
from source.analysis.provenance.native.native_sourcekit_dispatcher import NativeSourceKitDispatcher
from source.analysis.provenance.native.native_sourcekit_library import NativeSourceKitLibrary
from source.analysis.provenance.native.native_sourcekit_request import NativeSourceKitRequest
from stdio_incoming_messages import StdioIncomingMessages
from stdio_message_transport_runner import StdioMessageTransportRunner
from stdio_outgoing_message_factory import StdioOutgoingMessageFactory
from transport_format_detector import TransportFormatDetector


if __name__ == "__main__":
    library = NativeSourceKitLibrary(Path(sys.argv[1]))
    try:
        formats = TransportFormatDetector()
        StdioMessageTransportRunner(
            incoming=StdioIncomingMessages(RawStdinSource(), formats),
            stdout=RawStdoutSink(), format_detector=formats,
            dispatcher=NativeSourceKitDispatcher(
                decoder=PydanticModelDecoder(NativeSourceKitRequest),
                requests=library, responses=JsonRpcResponseBuilder(),
            ),
            outgoing_factory=StdioOutgoingMessageFactory(),
        ).run()
    finally:
        library.close()
