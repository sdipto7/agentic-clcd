"""
Pipeline 3: ReAct agent with autonomous skill loading and tool use.
"""

from __future__ import annotations

import os
import json
import time
from typing import Any, List

from tqdm import tqdm

from src.agent import build_react_executor
from src.constants import (
    ERROR,
    LABEL_TO_VERDICT,
    NOT_CLONE,
    PIPELINE_AGENTIC,
    OUTPUT_DIR_BY_PIPELINE,
)
from src.logger import get_logger
from src.result_writer import ResultWriter
from src.tools import (
    get_last_predicted_label,
    set_active_result_writer,
    was_write_result_called,
    clear_recorded_algorithms,
    get_recorded_algorithms,
)
from src.workflows.llm_helpers import pace_api_call

logger = get_logger(__name__)


def _save_algorithm_sidecar(
    model_alias: str,
    dataset_name: str,
    algorithms_by_pair: dict[str, dict[str, str]],
) -> None:
    """
    Write extracted algorithms for all pairs to a single JSON file.

    The output is written under the agentic output directory as
    ``algorithms_<model_alias>_<dataset_name>.json``.

    Args:
        model_alias: Model alias for the current run (used in filename).
        dataset_name: Dataset name for the current run (used in filename).
        algorithms_by_pair: Mapping of pair_id -> {"java_algorithm": ..., "python_algorithm": ...}.

    Returns:
        None.
    """
    out_dir = OUTPUT_DIR_BY_PIPELINE[PIPELINE_AGENTIC]
    os.makedirs(out_dir, exist_ok=True)

    json_name = f"algorithms_{model_alias}_{dataset_name}.json"
    json_path = os.path.join(out_dir, json_name)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(algorithms_by_pair, f, ensure_ascii=False, indent=2)


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

    for position, record in enumerate(tqdm(records, desc=f"agentic/{model_alias}"), start=1):
        set_active_result_writer(
            writer,
            pair_id=record["pair_id"],
            dataset=record["dataset"],
            ground_truth=record["label"],
        )

        t0 = time.perf_counter()

        try:
            executor.invoke({"input": _goal_message(record)})
        except Exception as exc:
            logger.exception("Agent crashed for pair %s: %s", record["pair_id"], exc)

        elapsed = time.perf_counter() - t0

        if not was_write_result_called():
            logger.warning(
                "Agent did not call write_result for %s; recording ERROR.",
                record["pair_id"],
            )

            writer.record_result(
                pair_id=record["pair_id"],
                dataset=record["dataset"],
                ground_truth=record["label"],
                predicted_label=ERROR,
                confidence=0.0,
                reasoning="Agent finished without write_result or tool failure.",
                processing_time_seconds=elapsed,
            )

        logger.info(
            "pair_id=%s pipeline=%s ground_truth=%s predicted=%s time=%.3fs",
            record["pair_id"],
            PIPELINE_AGENTIC,
            LABEL_TO_VERDICT.get(record["label"], NOT_CLONE),
            get_last_predicted_label() if was_write_result_called() else ERROR,
            elapsed,
        )

        set_active_result_writer(None)

        pace_api_call()

    # Save algorithms for the pairs for which the agent used the algo_based approach
    algorithms_by_pair = get_recorded_algorithms()
    if algorithms_by_pair:
        dataset_name = records[0]["dataset"] if records else "unknown_dataset"
        _save_algorithm_sidecar(model_alias, dataset_name, algorithms_by_pair)

        logger.info(
            "Agentic algorithms saved: %d/%d pairs used algo-based path.",
            len(algorithms_by_pair),
            len(records),
        )

    return writer.get_summary()
