"""Ollama HTTP client — localhost only."""
from __future__ import annotations

import json
import logging
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from finbot.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def is_ollama_available() -> bool:
    try:
        r = httpx.get(f"{settings.ollama_host}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def chat(
    messages: list[dict[str, str]],
    model: str | None = None,
    json_mode: bool = False,
    temperature: float = 0.7,
) -> str:
    """Send a chat request to Ollama. Raises RuntimeError if unavailable."""
    model = model or settings.ollama_model

    if not is_ollama_available():
        raise RuntimeError(
            "Ollama is not running. Start it with: ollama serve\n"
            "Then pull the model with: ollama pull " + model
        )

    payload: dict = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if json_mode:
        payload["format"] = "json"

    r = httpx.post(
        f"{settings.ollama_host}/api/chat",
        json=payload,
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    try:
        return data["message"]["content"]
    except (KeyError, TypeError) as e:
        logger.error("Unexpected Ollama response structure: %s", data)
        raise RuntimeError(f"Unexpected Ollama response: {e}") from e


def chat_structured(
    messages: list[dict[str, str]],
    response_model: type[T],
    model: str | None = None,
    temperature: float = 0.3,
    retries: int = 1,
) -> T | None:
    """Send a JSON-mode chat request and validate against a Pydantic model.

    Returns the validated model instance, or None if validation fails after retries.
    """
    for attempt in range(1 + retries):
        raw = chat(messages, model=model, json_mode=True, temperature=temperature)
        try:
            parsed = json.loads(raw)
            return response_model.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning("Structured output validation failed (attempt %d): %s", attempt + 1, e)
            if attempt < retries:
                messages = messages + [
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": f"Your response was not valid JSON matching the schema. Error: {e}. Please try again."},
                ]
    return None
