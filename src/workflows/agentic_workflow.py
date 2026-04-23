"""
Pipeline 3: ReAct agent with autonomous skill loading and tool use.
"""

from __future__ import annotations

import time
from typing import Any, List

from tqdm import tqdm

from src.agent import build_react_executor
from src.constants import (
    ERROR,
    LABEL_TO_VERDICT,
    NOT_CLONE,
    PIPELINE_AGENTIC,
)
from src.logger import get_logger
from src.result_writer import ResultWriter
from src.tools import (
    get_last_predicted_label,
    set_active_result_writer,
    was_write_result_called,
)
from src.workflows.llm_helpers import pace_api_call

logger = get_logger(__name__)


def _goal_message(rec: dict[str, Any]) -> str:
    """
    Format the detection task for the agent. The agent autonomously decides how to use its skills and tools to complete the task.

    Args:
        rec: a normalized dataset record with pair_id, codeA, codeB

    Returns:
        Goal string passed to the agent executor.
    """
    return (
        f"Determine whether the following Java and Python code fragments "
        f"are cross-language clones (pair ID: {rec['pair_id']}).\n\n"
        f"Java code:\n{rec['codeA']}\n\n"
        f"Python code:\n{rec['codeB']}\n\n"
        f"Use your available skills and tools to reach a verdict, "
        f"then record your final result using write_result."
    )


def run_agentic_workflow(
    llm: Any,
    records: List[dict[str, Any]],
    writer: ResultWriter,
    model_alias: str,
) -> dict[str, Any]:
    """
    Execute Pipeline 3: one ReAct episode per record.

    Args:
        llm: Chat model from :mod:`src.llm`.
        records: Normalized dataset rows.
        writer: ResultWriter for this run.
        model_alias: Model key for tqdm label.

    Returns:
        Summary dict from ``writer.get_summary()``.
    """
    executor = build_react_executor(llm)

    for position, rec in enumerate(tqdm(records, desc=f"agentic/{model_alias}"), start=1):
        set_active_result_writer(
            writer,
            pair_id=rec["pair_id"],
            dataset=rec["dataset"],
            ground_truth=rec["label"],
        )
        t0 = time.perf_counter()
        try:
            executor.invoke({"input": _goal_message(rec)})
        except Exception as exc:
            logger.exception("Agent crashed for pair %s: %s", rec["pair_id"], exc)
        elapsed = time.perf_counter() - t0

        if not was_write_result_called():
            logger.warning(
                "Agent did not call write_result for %s; recording ERROR.",
                rec["pair_id"],
            )
            writer.record_result(
                pair_id=rec["pair_id"],
                dataset=rec["dataset"],
                ground_truth=rec["label"],
                predicted_label=ERROR,
                confidence=0.0,
                reasoning="Agent finished without write_result or tool failure.",
                processing_time_seconds=elapsed,
            )

        gt_label = LABEL_TO_VERDICT.get(rec["label"], NOT_CLONE)
        predicted = get_last_predicted_label() if was_write_result_called() else ERROR
        logger.info(
            "pair_id=%s pipeline=%s ground_truth=%s predicted=%s time=%.3fs",
            rec["pair_id"],
            PIPELINE_AGENTIC,
            gt_label,
            predicted,
            elapsed,
        )

        if position % 10 == 0:
            summary = writer.get_summary()
            logger.info(
                "Progress checkpoint: %s pairs | running accuracy=%.4f",
                position,
                summary["accuracy"],
            )

        set_active_result_writer(None)
        pace_api_call()

    return writer.get_summary()
