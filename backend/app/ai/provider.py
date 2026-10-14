"""
LLM provider abstraction.

Every AI feature in this app (categorization fallback, insights, NL query)
talks to the LLM only through the `LLMProvider` interface below, never
directly to a vendor SDK. That keeps the vendor swappable (Groq, Gemini and
Anthropic are supported) and keeps every prompt/response boundary in one
place, which is what makes output validation and error handling tractable.

If no API key is configured, `get_llm_provider` returns `None` and callers
fall back to deterministic, template-based behavior (see app/ai/insights.py
and app/ai/query.py). This is what makes the app fully runnable without an
AI key.
"""
from abc import ABC, abstractmethod

from app.config import Settings


class AIProviderError(Exception):
    """Raised when the LLM provider fails to produce a usable response."""


class LLMProvider(ABC):
    """Minimal interface every LLM provider must implement."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        """Return the raw text completion for a system+user prompt pair."""
        raise NotImplementedError


# Hard ceiling on any single LLM call. Without it, a stalled network path or
# a chain of automatic SDK retries (e.g. on 429 rate limits) can leave a
# request hanging for minutes with no visible error. With it, a bad call
# fails fast and the app falls back to its template answer instead.
REQUEST_TIMEOUT_SECONDS = 20


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        # Imported lazily so the package is only required when this
        # provider is actually selected.
        from anthropic import Anthropic

        self._client = Anthropic(api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS, max_retries=1)
        self._model = model

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
            return "".join(parts).strip()
        except Exception as exc:  # noqa: BLE001 - we deliberately convert all provider errors
            raise AIProviderError(f"Anthropic API call failed: {exc}") from exc


class GeminiProvider(LLMProvider):
    """Google Gemini, via the free (no credit card required) Google AI
    Studio API tier. Get a key at https://aistudio.google.com/apikey.
    Set AI_PROVIDER=gemini and AI_MODEL=gemini-3.5-flash-lite (or another
    Gemini model name) in backend/.env to use this instead of Anthropic."""

    def __init__(self, api_key: str, model: str):
        # Imported lazily so the package is only required when this
        # provider is actually selected.
        from google import genai
        from google.genai import types

        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=REQUEST_TIMEOUT_SECONDS * 1000,  # milliseconds
                retry_options=types.HttpRetryOptions(attempts=2),
            ),
        )
        self._model = model

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        try:
            interaction = self._client.interactions.create(
                model=self._model,
                system_instruction=system_prompt,
                input=user_prompt,
                generation_config={"max_output_tokens": max_tokens},
            )
            return (interaction.output_text or "").strip()
        except Exception as exc:
            raise AIProviderError(f"Gemini API call failed: {exc}") from exc


class GroqProvider(LLMProvider):
    """Groq's free tier (no credit card required) via its OpenAI-compatible
    chat completions API - very low latency. Get a key at
    https://console.groq.com/keys, then set AI_PROVIDER=groq and
    AI_MODEL=openai/gpt-oss-20b in backend/.env.

    Called with plain httpx (already a dependency) rather than an SDK, so
    no extra package is needed."""

    ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
    # gpt-oss models are reasoning models: their hidden reasoning tokens
    # also count toward the completion limit, so leave headroom on top of
    # the visible-answer budget callers ask for.
    REASONING_HEADROOM_TOKENS = 512

    def __init__(self, api_key: str, model: str):
        import httpx

        self._httpx = httpx
        self._client = httpx.Client(
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        self._model = model

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        body = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_completion_tokens": max_tokens + self.REASONING_HEADROOM_TOKENS,
            "temperature": 0.2,
        }
        if self._model.startswith("openai/gpt-oss"):
            # Keep reasoning short (faster) and out of the returned text.
            body["reasoning_effort"] = "low"
            body["include_reasoning"] = False

        try:
            response = self._client.post(self.ENDPOINT, json=body)
        except self._httpx.HTTPError as exc:
            raise AIProviderError(f"Groq API call failed: {exc}") from exc

        if response.status_code != 200:
            raise AIProviderError(f"Groq API call failed: HTTP {response.status_code} - {response.text[:300]}")

        try:
            content = response.json()["choices"][0]["message"].get("content") or ""
        except (ValueError, KeyError, IndexError) as exc:
            raise AIProviderError(f"Groq API returned an unexpected response: {exc}") from exc
        return content.strip()


def get_llm_provider(settings: Settings) -> LLMProvider | None:
    """Factory: returns a configured provider, or None to signal 'use mock/fallback'."""
    if not settings.is_ai_configured:
        return None

    provider_name = settings.ai_provider.lower()
    if provider_name == "anthropic":
        return AnthropicProvider(api_key=settings.ai_api_key, model=settings.ai_model)
    if provider_name == "gemini":
        return GeminiProvider(api_key=settings.ai_api_key, model=settings.ai_model)
    if provider_name == "groq":
        return GroqProvider(api_key=settings.ai_api_key, model=settings.ai_model)

    # Unknown provider configured - fail safe to "no AI" rather than crash the app.
    return None
