"""
Chat model construction for OpenRouter (OpenAI-compatible API).

Every workflow obtains LLM instances through this module.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.constants import MODEL_MAP, OPENAI_API_BASE_URL

load_dotenv()


def create_chat_model(model_alias: str, temperature: float = 0.0) -> ChatOpenAI:
    """
    Build a ChatOpenAI client pointed at OpenRouter for the given model alias.

    Args:
        model_alias: Key in MODEL_MAP (e.g., ``deepseek_v3``).
        temperature: Sampling temperature; 0 for deterministic experiments.

    Returns:
        Configured ChatOpenAI instance.

    Raises:
        KeyError: If ``model_alias`` is not defined in MODEL_MAP.
        ValueError: If OPENROUTER_API_KEY is missing from the environment.
    """
    if model_alias not in MODEL_MAP:
        known = ", ".join(sorted(MODEL_MAP))
        raise KeyError(f"Unknown model alias {model_alias!r}. Choose one of: {known}")

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. Add it to your environment or .env file."
        )

    model_id = MODEL_MAP[model_alias]

    return ChatOpenAI(
        model=model_id,
        openai_api_key=api_key,
        openai_api_base=OPENAI_API_BASE_URL,
        temperature=temperature,
        timeout=120.0,
        max_retries=0,
    )
