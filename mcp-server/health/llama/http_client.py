"""
solid-description: Sends chat completion requests via HTTP and returns the parsed response.
solid-category: service
solid-tags: [hook, llm, http]
"""

from typing import Optional, Protocol

from llama.urllib_sender import HttpSending, UrllibSender
from llama.json_serializer import JsonSerializing, JsonSerializer
from llama.json_deserializer import JsonDeserializing, JsonDeserializer


class LlamaHttpChatting(Protocol):
    def chat(self, messages: list, tools: list, timeout: int) -> Optional[dict]: ...


class LlamaHttpClient:
    """POSTs to llama-server's /v1/chat/completions and returns the parsed response."""

    def __init__(
        self,
        host: str,
        model: str,
        inference_params: Optional[dict] = None,
        transport: Optional[HttpSending] = None,
        serializer: Optional[JsonSerializing] = None,
        deserializer: Optional[JsonDeserializing] = None,
    ) -> None:
        self._url = f"{host.rstrip('/')}/v1/chat/completions"
        self._model = model
        self._inference_params = inference_params or {}
        self._transport: HttpSending = transport or UrllibSender()
        self._serialize: JsonSerializing = serializer or JsonSerializer()
        self._deserialize: JsonDeserializing = deserializer or JsonDeserializer()

    def chat(self, messages: list, tools: list, timeout: int) -> Optional[dict]:
        payload = self._serialize.serialize({
            "model": self._model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            **self._inference_params,
        }).encode()
        try:
            raw = self._transport.send(
                self._url, payload, {"Content-Type": "application/json"}, timeout
            )
            return self._deserialize.deserialize(raw)
        except Exception:
            return None