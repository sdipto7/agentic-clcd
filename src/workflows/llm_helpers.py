"""
Shared LLM invocation helpers: retries, backoff, and message shaping.
"""

from __future__ import annotations

import time
from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage

from src.constants import API_CALL_DELAY_SECONDS, API_RETRY_BACKOFF_SECONDS
from src.logger import get_logger

logger = get_logger(__name__)


def invoke_chat_text(llm: BaseChatModel, user_text: str) -> str:
    """
    Send a single human message and return string content from the assistant.

    Args:
        llm: Chat model instance.
        user_text: Full prompt body.

    Returns:
        Model response content (possibly empty string).
    """
    messages: List[BaseMessage] = [HumanMessage(content=user_text)]
    response = llm.invoke(messages)
    content = getattr(response, "content", response)
    if isinstance(content, list):
        # Some providers return chunk lists
        parts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content) if content is not None else ""


def invoke_with_single_retry(llm: BaseChatModel, user_text: str) -> str:
    """
    Call ``invoke_chat_text`` with one retry after API failures.

    Args:
        llm: Chat model instance.
        user_text: Full prompt body.

    Returns:
        Model text, or empty string if both attempts fail.
    """
    try:
        return invoke_chat_text(llm, user_text)
    except Exception as first_exc:
        logger.warning(
            "LLM call failed (%s). Retrying after %.1fs...",
            first_exc,
            API_RETRY_BACKOFF_SECONDS,
        )
        time.sleep(API_RETRY_BACKOFF_SECONDS)
        try:
            return invoke_chat_text(llm, user_text)
        except Exception as second_exc:
            logger.error("LLM call failed again: %s", second_exc)
            return ""


def pace_api_call() -> None:
    """Sleep for the configured delay between successful calls."""
    time.sleep(API_CALL_DELAY_SECONDS)
