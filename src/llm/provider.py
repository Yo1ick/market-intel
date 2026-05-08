from dataclasses import dataclass
from typing import Protocol
from openai import OpenAI


@dataclass
class LLMResponse:
    content: str | None = None
    tool_calls: list[dict] | None = None


class LLMProvider(Protocol):
    def generate(
        self, messages: list[dict], tools: list[dict] | None = None, temperature: float = 0.3
    ) -> LLMResponse: ...


class OpenAICompatibleProvider:
    def __init__(self, model: str, base_url: str, api_key: str) -> None:
        self._model = model
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    def generate(
        self, messages: list[dict], tools: list[dict] | None = None, temperature: float = 0.3
    ) -> LLMResponse:

        kwargs = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools

        response = self._client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        tool_calls = [tc.model_dump() for tc in message.tool_calls] if message.tool_calls else None
        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
        )
