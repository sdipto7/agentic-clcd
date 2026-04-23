"""
Direct Pipeline: direct single-call clone detection per pair.
"""

from __future__ import annotations

import time
from typing import Any, List

from tqdm import tqdm

from src.constants import (
    ERROR,
    LABEL_TO_VERDICT,
    NOT_CLONE,
    PIPELINE_DIRECT,
)
from src.logger import get_logger
from src.prompts import DIRECT_DETECTION_PROMPT
from src.result_writer import ResultWriter
from src.workflows.llm_helpers import invoke_with_single_retry, pace_api_call
from src.workflows.llm_response_parser import interpret_detection_response

logger = get_logger(__name__)


def _log_progress(processed: int, writer: ResultWriter) -> None:
    """Emit aggregate accuracy every 10 pairs."""
    if processed == 0 or processed % 10 != 0:
        return
    summary = writer.get_summary()
    acc = summary["accuracy"]
    logger.info(
        "Progress checkpoint: %s pairs processed | running accuracy=%.4f",
        processed,
        acc,
    )


def run_direct_workflow(
    llm: Any,
    records: List[dict[str, Any]],
    writer: ResultWriter,
    model_alias: str,
) -> dict[str, Any]:
    """
    Execute Direct Pipeline over all records.

    Args:
        llm: Chat model from :mod:`src.llm`.
        records: Normalized dataset rows.
        writer: ResultWriter for this run.
        model_alias: Model key (for logging only; already on writer).

    Returns:
        Summary dict from ``writer.get_summary()``.
    """
    for position, record in enumerate(tqdm(records, desc=f"direct/{model_alias}"), start=1):
        t0 = time.perf_counter()
        prompt = DIRECT_DETECTION_PROMPT.format(codeA=record["codeA"], codeB=record["codeB"])
        raw = invoke_with_single_retry(llm, prompt)
        elapsed = time.perf_counter() - t0

        if not raw.strip():
            verdict, confidence, reasoning = ERROR, 0.5, "LLM call failed after retry."
            logger.error("Empty LLM response for pair %s", record["pair_id"])
        else:
            verdict, confidence, reasoning = interpret_detection_response(raw)

        writer.record_result(
            pair_id=record["pair_id"],
            dataset=record["dataset"],
            ground_truth=record["label"],
            predicted_label=verdict,
            confidence=confidence,
            reasoning=reasoning,
            processing_time_seconds=elapsed,
        )

        gt_label = LABEL_TO_VERDICT.get(record["label"], NOT_CLONE)
        logger.info(
            "pair_id=%s pipeline=%s ground_truth=%s predicted=%s time=%.3fs",
            record["pair_id"],
            PIPELINE_DIRECT,
            gt_label,
            verdict,
            elapsed,
        )

        _log_progress(position, writer)
        pace_api_call()

    return writer.get_summary()
