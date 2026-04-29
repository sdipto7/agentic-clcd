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
_algorithms_by_pair: dict[str, dict[str, str]] = {}


def get_recorded_algorithms() -> dict[str, dict[str, str]]:
    """Return all recorded algorithms collected during the run."""
    return _algorithms_by_pair


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
    global _active_writer, _context_pair_id, _context_dataset, _context_ground_truth
    global _pair_start_time, _write_result_called, _last_predicted_label

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
    Return all available skills with their names and descriptions.
    Call this when you are unsure what skills exist or want to decide which skill is relevant for your current task.

    Returns:
        A formatted list of skill names and their descriptions.
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
    Retrieve the full instructions for a skill by name.
    Call this before performing any task that a skill covers - never assume skill content without loading it first.
    Use list_skills first if you are unsure of the exact skill name.

    Args:
        skill_name: exact name from the skill list (e.g., algorithm_extraction).
    Returns:
        Full skill instructions as plain text, or an error message if not found.
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
    Display two code fragments or algorithms side by side for comparison.
    Call this when you need to analyze two pieces of content together before making a clone detection decision.

    Args:
        content_a: first fragment - Java source code or Algorithm A.
        content_b: second fragment - Python source code or Algorithm B.
        comparison_type: "source_code" when comparing raw code, "algorithm" when comparing extracted pseudocode.
    Returns:
        A formatted string showing both fragments labeled and side by side.
    """
    comparison_type = comparison_type.strip()
    if comparison_type not in (COMPARE_TYPE_SOURCE_CODE, COMPARE_TYPE_ALGORITHM):
        return (
            f"Invalid comparison_type {comparison_type!r}. "
            f'Use "{COMPARE_TYPE_SOURCE_CODE}" or "{COMPARE_TYPE_ALGORITHM}".'
        )

    label_left = "Java" if comparison_type == COMPARE_TYPE_SOURCE_CODE else "Algorithm A (Java side)"
    label_right = "Python" if comparison_type == COMPARE_TYPE_SOURCE_CODE else "Algorithm B (Python side)"

    return (
        f"=== {label_left} ===\n{content_a.strip()}\n\n"
        f"=== {label_right} ===\n{content_b.strip()}\n"
    )


@tool
def write_result(verdict: str, confidence: float, reasoning: str) -> str:
    """
    Record the final clone detection verdict for the current pair. Call this exactly once after you have completed your analysis
    and formed a final judgment. Do not call this more than once per pair - duplicate calls will be rejected.

    Args:
        verdict: must be exactly CLONE or NOT_CLONE.
        confidence: how confident you are in the verdict, between 0.0 and 1.0.
        reasoning: brief explanation of your decision in max 100 words.
    Returns:
        Confirmation message if recorded successfully, or an error description.
    """
    global _write_result_called, _last_predicted_label

    if _write_result_called:
        return "A result was already recorded for this pair; do not call write_result again."

    if _active_writer is None:
        return "No active result writer configured; cannot record."

    if _context_pair_id is None or _context_dataset is None or _context_ground_truth is None:
        return "Internal error: pair context missing for write_result."

    verdict = verdict.strip().upper()
    if verdict in ("NOT CLONE", "NON_CLONE"):
        verdict = "NOT_CLONE"

    if verdict not in ("CLONE", "NOT_CLONE"):
        return f"Invalid verdict {verdict!r}; use CLONE or NOT_CLONE."

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = max(0.0, min(1.0, confidence))

    elapsed = 0.0
    if _pair_start_time is not None:
        elapsed = time.perf_counter() - _pair_start_time

    _active_writer.record_result(
        pair_id=_context_pair_id,
        dataset=_context_dataset,
        ground_truth=_context_ground_truth,
        predicted_label=verdict,
        confidence=confidence,
        reasoning=reasoning,
        processing_time_seconds=elapsed,
    )
    _write_result_called = True
    _last_predicted_label = verdict

    logger.info(
        "write_result tool: pair_id=%s ground_truth=%s predicted=%s conf=%.3f time=%.3fs",
        _context_pair_id,
        _context_ground_truth,
        verdict,
        confidence,
        elapsed,
    )

    return f"Recorded result for {_context_pair_id}: {verdict} (confidence {confidence:.3f})."


@tool
def record_algorithms(java_algorithm: str, python_algorithm: str) -> str:
    """
    Save the extracted pseudocode algorithms for the current pair.
    Call this exactly once per pair, and only after algorithms from
    BOTH the Java and Python code fragment is fully extracted. Do not
    call this if only one algorithm has been extracted - wait until both
    are ready. Only call this when using the algorithm-based detection path.
    Do not call this on direct detection runs.

    Args:
        java_algorithm: pseudocode extracted from the Java fragment.
        python_algorithm: pseudocode extracted from the Python fragment.
    Returns:
        Confirmation message if saved successfully.
    """
    if _context_pair_id is None:
        return "No active pair context; cannot record algorithms."

    if _context_pair_id in _algorithms_by_pair:
        return (
            f"Algorithms already recorded for {_context_pair_id}. "
            "Do not call record_algorithms more than once per pair."
        )

    if not java_algorithm.strip() or not python_algorithm.strip():
        return (
            "Both java_algorithm and python_algorithm must be non-empty. "
            "Extract algorithms from both fragments before calling this tool."
        )

    _algorithms_by_pair[_context_pair_id] = {
        "java_algorithm": java_algorithm.strip(),
        "python_algorithm": python_algorithm.strip(),
    }

    return f"Recorded algorithms for {_context_pair_id}."


def get_agent_tools() -> list[Any]:
    """Return all BaseTool instances used by Pipeline 3."""
    return [list_skills, load_skill, compare_and_decide, write_result, record_algorithms]
