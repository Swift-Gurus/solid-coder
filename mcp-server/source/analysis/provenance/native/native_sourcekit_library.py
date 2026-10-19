"""Adapts the installed SourceKit C request API inside an isolated worker."""

import ctypes
from pathlib import Path

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing


"""
solid-name: NativeSourceKitLibrary
solid-category: boundary-adapter
solid-spec: [SPEC-064]
solid-description: Exchanges native semantic requests while releasing request, response, and diagnostic memory across successful and failed calls.
"""
class NativeSourceKitLibrary(SourceSyntaxParsing[str, str]):
    def __init__(self, path: Path) -> None:
        self._api = ctypes.CDLL(str(path))
        self._memory = ctypes.CDLL(None)
        self._memory.free.argtypes = [ctypes.c_void_p]
        self._memory.free.restype = None
        self._api.sourcekitd_initialize.argtypes = []
        self._api.sourcekitd_initialize.restype = None
        self._api.sourcekitd_shutdown.argtypes = []
        self._api.sourcekitd_shutdown.restype = None
        self._api.sourcekitd_request_create_from_yaml.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p)]
        self._api.sourcekitd_request_create_from_yaml.restype = ctypes.c_void_p
        self._api.sourcekitd_send_request_sync.argtypes = [ctypes.c_void_p]
        self._api.sourcekitd_send_request_sync.restype = ctypes.c_void_p
        self._api.sourcekitd_response_description_copy.argtypes = [ctypes.c_void_p]
        self._api.sourcekitd_response_description_copy.restype = ctypes.c_void_p
        self._api.sourcekitd_response_is_error.argtypes = [ctypes.c_void_p]
        self._api.sourcekitd_response_is_error.restype = ctypes.c_bool
        self._api.sourcekitd_response_dispose.argtypes = [ctypes.c_void_p]
        self._api.sourcekitd_response_dispose.restype = None
        self._api.sourcekitd_request_release.argtypes = [ctypes.c_void_p]
        self._api.sourcekitd_request_release.restype = None
        self._api.sourcekitd_initialize()

    def parse(self, source: str) -> str:
        error = ctypes.c_char_p()
        request = self._api.sourcekitd_request_create_from_yaml(source.encode(), ctypes.byref(error))
        if not request:
            try:
                raise ValueError(error.value.decode() if error.value else "Invalid native semantic request.")
            finally:
                self._memory.free(error)
        try:
            response = self._api.sourcekitd_send_request_sync(request)
            if not response:
                raise ConnectionError("The native semantic service returned no response.")
            try:
                description = self._api.sourcekitd_response_description_copy(response)
                if not description:
                    raise ConnectionError("The native semantic service omitted its response content.")
                try:
                    result = ctypes.string_at(description).decode()
                finally:
                    self._memory.free(description)
                if self._api.sourcekitd_response_is_error(response):
                    raise ConnectionError(result)
                return result
            finally:
                self._api.sourcekitd_response_dispose(response)
        finally:
            self._api.sourcekitd_request_release(request)

    def close(self) -> None:
        self._api.sourcekitd_shutdown()
