#!/usr/bin/env python3
"""
Run cross-language clone-detection experiments across pipelines, models, and datasets.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Callable, Dict, List
import time
from langchain_community.callbacks import get_openai_callback

_PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.constants import (  # noqa: E402
    DATASET_CHOICES,
    MODEL_CHOICES,
    PIPELINE_AGENTIC,
    PIPELINE_ALGO_BASED,
    PIPELINE_CHOICES,
    PIPELINE_DIRECT,
)
from src.result_helper import results_csv_path, prepare_records_to_run  # noqa: E402
from src.dataset_loader import DatasetLoader  # noqa: E402
from src.llm import create_chat_model  # noqa: E402
from src.logger import get_logger, setup_logging  # noqa: E402
from src.result_writer import ResultWriter  # noqa: E402
from src.workflows.agentic_workflow import run_agentic_workflow  # noqa: E402
from src.workflows.algo_based_workflow import run_algo_based_workflow  # noqa: E402
from src.workflows.direct_workflow import run_direct_workflow  # noqa: E402
from src.token_usage_writer import save_token_usage_data  # noqa: E402


logger = get_logger(__name__)

WorkflowFn = Callable[[Any, List[dict[str, Any]], ResultWriter, str], dict[str, Any]]

WORKFLOW_REGISTRY: Dict[str, WorkflowFn] = {
    PIPELINE_DIRECT: run_direct_workflow,
    PIPELINE_ALGO_BASED: run_algo_based_workflow,
    PIPELINE_AGENTIC: run_agentic_workflow,
}


def main() -> None:
    """
    Command-line entry point for running one experiment.

    Required CLI arguments:
    - pipeline: direct, algo_based, agentic
    - model: one of the available model aliases (see MODEL_CHOICES in src/constants.py)
    - dataset: xlcost, codenet

    Example:
        python main.py --pipeline direct --model deepseek_v3 --dataset xlcost

    Returns:
        None.
    """
    setup_logging()

    parser = argparse.ArgumentParser(description="Cross-language clone detection experiments.")
    parser.add_argument(
        "--pipeline",
        choices=[c for c in PIPELINE_CHOICES if c != "all"],
        required=True,
        help="Pipeline to run.",
    )
    parser.add_argument(
        "--model",
        choices=[c for c in MODEL_CHOICES if c != "all"],
        required=True,
        help="Model alias to use.",
    )
    parser.add_argument(
        "--dataset",
        choices=[c for c in DATASET_CHOICES if c != "all"],
        required=True,
        help="Dataset to evaluate.",
    )
    args = parser.parse_args()

    pipeline = args.pipeline
    model_alias = args.model
    dataset_name = args.dataset

    runner = WORKFLOW_REGISTRY[pipeline]
    llm = create_chat_model(model_alias)

    loader = DatasetLoader(dataset_name)
    try:
        records = loader.load()
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return

    csv_path = results_csv_path(pipeline, model_alias, dataset_name)

    records_to_run = prepare_records_to_run(records, csv_path)
    if not records_to_run:
        logger.info("All pairs are already processed successfully.")
        return

    writer = ResultWriter(csv_path, pipeline=pipeline, model_alias=model_alias)

    logger.info(
        "Starting run pipeline=%s model=%s dataset=%s pairs=%s",
        pipeline,
        model_alias,
        dataset_name,
        len(records_to_run),
    )

    t0 = time.perf_counter()
    summary: dict[str, Any] | None = None
    run_status = "success"

    with get_openai_callback() as cb:
        try:
            summary = runner(llm, records_to_run, writer, model_alias)
        except KeyboardInterrupt:
            run_status = "interrupted"
            raise
        except Exception:
            run_status = "crashed"
            logger.exception("Run crashed")
            raise
        finally:
            elapsed_seconds = time.perf_counter() - t0
            if summary is None:
                summary = writer.get_summary()

            save_token_usage_data(
                pipeline=pipeline,
                model_alias=model_alias,
                dataset=dataset_name,
                pairs=len(records_to_run),
                elapsed_seconds=elapsed_seconds,
                run_status=run_status,
                token_usage={
                    "prompt_tokens": cb.prompt_tokens,
                    "completion_tokens": cb.completion_tokens,
                    "total_tokens": cb.total_tokens,
                    "successful_requests": cb.successful_requests,
                    "total_cost": cb.total_cost,
                },
                metrics=summary,
            )



if __name__ == "__main__":
    main()
