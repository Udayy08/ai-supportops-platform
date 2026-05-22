"""
Provider-agnostic LLM factory.

Currently supports Groq (ChatGroq). Designed so that swapping to OpenAI,
Anthropic, or any other LangChain-compatible provider requires only adding
a new branch — zero changes to agent node code.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage

from app.config import settings

def parse_json_response(response: BaseMessage) -> dict:
    """Safely parse JSON from an LLM response, stripping markdown blocks."""
    content = response.content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    import json
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"FAILED TO PARSE JSON: {e}\nRAW CONTENT: {response.content}")
        return {}



LLMProvider = Literal["groq"]


def get_llm(
    provider: LLMProvider = "groq",
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 1024,
    **kwargs,
) -> BaseChatModel:
    """
    Return a LangChain chat model instance.

    This is the ONLY place in the codebase that knows about concrete LLM
    providers. Every agent node calls `get_llm()` and receives a generic
    `BaseChatModel`.

    Args:
        provider:    LLM provider identifier.
        model:       Model name override. Falls back to settings default.
        temperature: Sampling temperature.
        max_tokens:  Maximum generation tokens.
    """
    if provider == "groq":
        return ChatGroq(
            api_key=settings.groq_api_key,
            model=model or settings.groq_default_model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
    # ── Future providers ─────────────────────────────────────────────────
    # elif provider == "openai":
    #     from langchain_openai import ChatOpenAI
    #     return ChatOpenAI(api_key=settings.openai_api_key, model=model or "gpt-4o", ...)
    # elif provider == "anthropic":
    #     from langchain_anthropic import ChatAnthropic
    #     return ChatAnthropic(...)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_fast_llm(provider: LLMProvider = "groq", **kwargs) -> BaseChatModel:
    """Convenience: return the smaller, faster model for lightweight tasks."""
    model = settings.groq_fast_model if provider == "groq" else None
    return get_llm(provider=provider, model=model, **kwargs)
