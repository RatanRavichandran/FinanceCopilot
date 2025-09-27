from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, MutableMapping, Sequence

from ..config import AppSettings, get_settings


class LLMUnavailable(RuntimeError):
    """Raised when the Large Language Model client cannot be initialised."""


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str

    def as_dict(self) -> dict[str, str]:  # pragma: no cover - thin wrapper
        return {"role": self.role, "content": self.content}


def _build_client(settings: AppSettings):
    if not settings.openai_api_key:
        raise LLMUnavailable("Missing OPENAI_API_KEY environment variable.")

    try:  # prefer the latest SDK
        from openai import OpenAI  # type: ignore

        return OpenAI(api_key=settings.openai_api_key), True
    except ImportError:  # pragma: no cover - legacy fallback
        import openai  # type: ignore

        openai.api_key = settings.openai_api_key
        return openai, False


def chat(
    messages: Sequence[ChatMessage | Mapping[str, str]],
    *,
    model: str | None = None,
    max_tokens: int | None = 400,
    temperature: float = 0.7,
    extra_params: MutableMapping[str, object] | None = None,
) -> str:
    """Execute a chat completion request and return the assistant content."""

    settings = get_settings()
    client, _ = _build_client(settings)

    payload: dict[str, object] = {
        "model": model or settings.openai_model,
        "messages": [m.as_dict() if isinstance(m, ChatMessage) else dict(m) for m in messages],
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if extra_params:
        payload.update(extra_params)

    try:
        response = client.chat.completions.create(**payload)  # type: ignore[attr-defined]
    except Exception as exc:  # pragma: no cover - network failures are surfaced to UI
        raise RuntimeError(f"Unable to complete chat request: {exc}") from exc

    choice = response.choices[0]
    return choice.message.content.strip()


__all__ = ["ChatMessage", "LLMUnavailable", "chat"]
