"""
LangChain tools for the Pipeline 3 ReAct agent: skills, comparison helper, result I/O.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from langchain_core.tools import tool

from src.constants import (
    COMPARE_TYPE_ALGORITHM,
    COMPARE_TYPE_SOURCE_CODE,
)
from src.logger import get_logger
from src.result_writer import ResultWriter
from src.skills import SKILL_REGISTRY

logger = get_logger(__name__)

_skill_body_cache: dict[str, str] = {}
_active_writer: Optional[ResultWriter] = None
_context_pair_id: Optional[str] = None
_context_dataset: Optional[str] = None
_context_ground_truth: Optional[int] = None
_pair_start_time: Optional[float] = None
_write_result_called: bool = False
_last_predicted_label: Optional[str] = None


def set_active_result_writer(
    writer: Optional[ResultWriter],
    pair_id: Optional[str] = None,
    dataset: Optional[str] = None,
    ground_truth: Optional[int] = None,
) -> None:
    """
    Bind the ResultWriter and current pair metadata before each agent invocation.

    Args:
        writer: Writer instance for this run, or None to clear.
        pair_id: Identifier for the active pair.
        dataset: Dataset name for the active pair.
        ground_truth: 1 clone, 0 non-clone.
    """
    global _active_writer, _context_pair_id, _context_dataset
    global _context_ground_truth, _pair_start_time, _write_result_called
    global _last_predicted_label
    _active_writer = writer
    _context_pair_id = pair_id
    _context_dataset = dataset
    _context_ground_truth = ground_truth
    _pair_start_time = time.perf_counter() if writer is not None else None
    _write_result_called = False
    _last_predicted_label = None


def was_write_result_called() -> bool:
    """Return True if the agent invoked ``write_result`` for the current pair."""
    return _write_result_called


def get_last_predicted_label() -> Optional[str]:
    """Return the verdict last written by ``write_result`` for the active pair, if any."""
    return _last_predicted_label


@tool
def list_skills() -> str:
    """
    List skills available in the registry with short descriptions.

    Call this first to decide which specialized instructions to load next.
    """
    if not SKILL_REGISTRY:
        return "No skills were discovered on disk."
    lines = ["Available skills (call load_skill with the name):"]
    for info in sorted(SKILL_REGISTRY.values(), key=lambda x: x["name"]):
        lines.append(f"- {info['name']}: {info['description']}")
    return "\n".join(lines)


@tool
def load_skill(skill_name: str) -> str:
    """
    Load the full markdown instructions for a named skill.

    Args:
        skill_name: Exact `name` from skill front matter (e.g., algorithm_extraction).

    Returns:
        Skill body text, or an error message if unknown.
    """
    if skill_name in _skill_body_cache:
        return _skill_body_cache[skill_name]
    entry = SKILL_REGISTRY.get(skill_name.strip())
    if not entry:
        known = ", ".join(sorted(SKILL_REGISTRY.keys())) or "(none)"
        return f"Unknown skill {skill_name!r}. Known skills: {known}"
    body = entry["body"]
    _skill_body_cache[skill_name] = body
    logger.info("Skill loaded into cache: %s", skill_name)
    return body


@tool
def compare_and_decide(content_a: str, content_b: str, comparison_type: str) -> str:
    """
    Present two texts side by side for manual reasoning (no LLM call inside the tool).

    Args:
        content_a: First fragment (e.g., Java source or Algorithm A).
        content_b: Second fragment (e.g., Python source or Algorithm B).
        comparison_type: Either "source_code" or "algorithm" (controls labels only).

    Returns:
        A formatted string suitable for reading in the agent trace.
    """
    ct = comparison_type.strip()
    if ct not in (COMPARE_TYPE_SOURCE_CODE, COMPARE_TYPE_ALGORITHM):
        return (
            f"Invalid comparison_type {comparison_type!r}. "
            f'Use "{COMPARE_TYPE_SOURCE_CODE}" or "{COMPARE_TYPE_ALGORITHM}".'
        )
    label_left = "Java" if ct == COMPARE_TYPE_SOURCE_CODE else "Algorithm A (Java side)"
    label_right = "Python" if ct == COMPARE_TYPE_SOURCE_CODE else "Algorithm B (Python side)"
    return (
        f"=== {label_left} ===\n{content_a.strip()}\n\n"
        f"=== {label_right} ===\n{content_b.strip()}\n"
    )


@tool
def write_result(predicted_label: str, confidence: float, reasoning: str) -> str:
    """
    Persist one clone-detection outcome via the active ResultWriter.

    Call only after you have followed the skills and formed a final judgment.
    predicted_label must be CLONE or NOT_CLONE (uppercase recommended).

    Args:
        predicted_label: CLONE or NOT_CLONE.
        confidence: Value between 0.0 and 1.0.
        reasoning: At most ~100 words; keep concise.

    Returns:
        Confirmation string, or an error description.
    """
    global _write_result_called, _last_predicted_label
    if _write_result_called:
        return "A result was already recorded for this pair; do not call write_result again."
    if _active_writer is None:
        return "No active result writer configured; cannot record."
    if _context_pair_id is None or _context_dataset is None or _context_ground_truth is None:
        return "Internal error: pair context missing for write_result."

    pred = predicted_label.strip().upper()
    if pred in ("NOT CLONE", "NON_CLONE"):
        pred = "NOT_CLONE"
    if pred not in ("CLONE", "NOT_CLONE"):
        return f"Invalid predicted_label {predicted_label!r}; use CLONE or NOT_CLONE."

    try:
        conf = float(confidence)
    except (TypeError, ValueError):
        conf = 0.5
    conf = max(0.0, min(1.0, conf))

    elapsed = 0.0
    if _pair_start_time is not None:
        elapsed = time.perf_counter() - _pair_start_time

    _active_writer.record_result(
        pair_id=_context_pair_id,
        dataset=_context_dataset,
        ground_truth=_context_ground_truth,
        predicted_label=pred,
        confidence=conf,
        reasoning=reasoning,
        processing_time_seconds=elapsed,
    )
    _write_result_called = True
    _last_predicted_label = pred
    logger.info(
        "write_result tool: pair_id=%s ground_truth=%s predicted=%s conf=%.3f time=%.3fs",
        _context_pair_id,
        _context_ground_truth,
        pred,
        conf,
        elapsed,
    )
    return f"Recorded result for {_context_pair_id}: {pred} (confidence {conf:.3f})."


def get_agent_tools() -> list[Any]:
    """Return all BaseTool instances used by Pipeline 3."""
    return [list_skills, load_skill, compare_and_decide, write_result]
