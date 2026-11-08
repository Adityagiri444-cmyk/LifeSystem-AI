try:
    import httpx
except ImportError:  # keep the app running (template fallback) if httpx isn't installed
    httpx = None

from app.config import settings


class LLMError(Exception):
    """Any failure talking to the LLM. Callers fall back to templates."""


def llm_configured() -> bool:
    return bool(settings.llm_base_url and settings.llm_api_key and settings.llm_model)


def call_llm(system: str, user: str) -> str:
    """
    Send one chat request to any OpenAI-compatible endpoint (Groq, Gemini's OpenAI
    endpoint, OpenRouter, a local Ollama server, ...) and return the reply text.
    Raises LLMError on any problem. The key is never logged.
    """
    if httpx is None:
        raise LLMError("httpx_missing")
    if not llm_configured():
        raise LLMError("not_configured")

    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    body = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": 300,
    }
    headers = {"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"}

    try:
        response = httpx.post(url, json=body, headers=headers, timeout=settings.llm_timeout_seconds)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        raise LLMError(f"http_{e.response.status_code}") from None
    except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError):
        raise LLMError("request_failed") from None