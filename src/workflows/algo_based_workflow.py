"""
Pipeline 2: extract algorithms per fragment, compare in a third LLM call.
"""

from __future__ import annotations

import os
import time
from typing import Any, List

from tqdm import tqdm

from src.constants import (
    ERROR,
    JAVA_LANGUAGE_IDENTIFIER,
    PYTHON_LANGUAGE_IDENTIFIER,
    LABEL_TO_VERDICT,
    NOT_CLONE,
    OUTPUT_DIR_BY_PIPELINE,
    PIPELINE_ALGO_BASED,
)
from src.logger import get_logger
from src.prompts import ALGO_DETECTION_PROMPT, ALGO_EXTRACTION_PROMPT
from src.result_writer import ResultWriter
from src.workflows.llm_helpers import invoke_with_single_retry, pace_api_call
from src.workflows.llm_response_parser import interpret_llm_response

logger = get_logger(__name__)


def _save_algorithm_sidecar(pair_id: str, side: str, text: str) -> None:
    """Persist extracted algorithm text next to other algo_based artifacts."""
    out_dir = OUTPUT_DIR_BY_PIPELINE[PIPELINE_ALGO_BASED]
    os.makedirs(out_dir, exist_ok=True)
    fname = f"{pair_id}_{side}_algorithm.txt"
    path = os.path.join(out_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def run_algo_based_workflow(
    llm: Any,
    records: List[dict[str, Any]],
    writer: ResultWriter,
    model_alias: str,
) -> dict[str, Any]:
    """
    Execute Algorithm-Based Pipeline (three calls per pair) over all records.

    Args:
        llm: Chat model from :mod:`src.llm`.
        records: Normalized dataset rows.
        writer: ResultWriter for this run.
        model_alias: Model key for tqdm label.

    Returns:
        Summary dict from ``writer.get_summary()``.
    """
    for position, record in enumerate(tqdm(records, desc=f"algo_based/{model_alias}"), start=1):
        t0 = time.perf_counter()
        pair_id = record["pair_id"]

        java_to_algo_extraction_prompt = ALGO_EXTRACTION_PROMPT.format(language=JAVA_LANGUAGE_IDENTIFIER, source_code=record["codeA"])
        py_to_algo_extraction_prompt = ALGO_EXTRACTION_PROMPT.format(language=PYTHON_LANGUAGE_IDENTIFIER, source_code=record["codeB"])

        algo_java = invoke_with_single_retry(llm, java_to_algo_extraction_prompt).strip()
        pace_api_call()
        
        algo_py = invoke_with_single_retry(llm, py_to_algo_extraction_prompt).strip()
        pace_api_call()

        if not algo_java:
            algo_java = "(extraction failed — empty response)"
            logger.error("Java algorithm extraction empty for %s", pair_id)

        if not algo_py:
            algo_py = "(extraction failed — empty response)"
            logger.error("Python algorithm extraction empty for %s", pair_id)

        _save_algorithm_sidecar(pair_id, "java", algo_java)
        _save_algorithm_sidecar(pair_id, "python", algo_py)

        clone_detection_prompt = ALGO_DETECTION_PROMPT.format(algorithm_a=algo_java, algorithm_b=algo_py)

        llm_response_raw = invoke_with_single_retry(llm, clone_detection_prompt)

        elapsed = time.perf_counter() - t0

        if not llm_response_raw.strip():
            verdict, confidence, reasoning = ERROR, 0.5, "LLM compare call failed after retry."
            logger.error("Empty compare response for pair %s", pair_id)
        else:
            verdict, confidence, reasoning = interpret_llm_response(llm_response_raw)

        writer.record_result(
            pair_id=pair_id,
            dataset=record["dataset"],
            ground_truth=record["label"],
            predicted_label=verdict,
            confidence=confidence,
            reasoning=reasoning,
            processing_time_seconds=elapsed,
        )

        logger.info(
            "pair_id=%s pipeline=%s ground_truth=%s predicted=%s time=%.3fs",
            pair_id,
            PIPELINE_ALGO_BASED,
            LABEL_TO_VERDICT.get(record["label"], NOT_CLONE),
            verdict,
            elapsed,
        )

        pace_api_call()

    return writer.get_summary()
